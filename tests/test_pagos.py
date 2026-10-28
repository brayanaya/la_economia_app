import hashlib
from decimal import Decimal

from app.core.config import settings
from app.pagos.wompi import (
    calcular_checksum_evento,
    construir_firma_integridad,
    monto_centavos,
)

from tests.test_ordenes_consulta import payload_orden


async def _crear_orden(cliente, **cambios):
    cuerpo = payload_orden(metodo_pago="wompi", **cambios)
    respuesta = await cliente.post("/api/v1/ordenes/", json=cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def _iniciar_pago(cliente, orden_id):
    respuesta = await cliente.post(
        f"/api/v1/pagos/ordenes/{orden_id}/iniciar", json={"metodo": "wompi"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _evento_wompi(referencia, monto, estado="APPROVED", transaccion_id="trans-123"):
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": transaccion_id,
                "status": estado,
                "reference": referencia,
                "amount_in_cents": monto,
                "currency": "COP",
            }
        },
        "signature": {
            "properties": [
                "transaction.id",
                "transaction.status",
                "transaction.amount_in_cents",
                "transaction.reference",
            ],
            "checksum": "",
        },
    }


def _firmar_evento(evento, secreto):
    evento["signature"]["checksum"] = calcular_checksum_evento(
        evento, evento["signature"]["properties"], secreto
    )
    return evento


async def test_monto_centavos():
    assert monto_centavos(Decimal("10500.00")) == 1050000
    assert monto_centavos(Decimal("0.99")) == 99
    assert monto_centavos(Decimal("1.005")) == 101  # redondeo half-up: 1.005 * 100 = 100.5 -> 101


async def test_firma_de_integridad_con_vDocumento_conocido():
    firma = construir_firma_integridad(450000, "COP", "LEA-ABC-01", "secreto")
    esperada = hashlib.sha256(b"450000COPLEA-ABC-01secreto").hexdigest()
    assert firma == esperada


async def test_iniciar_pago_sin_pasarela_configurada_da_503(cliente_autenticado):
    orden = await _crear_orden(cliente_autenticado)
    respuesta = await cliente_autenticado.post(
        f"/api/v1/pagos/ordenes/{orden['id']}/iniciar", json={"metodo": "wompi"}
    )
    assert respuesta.status_code == 503


async def test_iniciar_pago_devuelve_formulario_con_firma(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])

    assert inicio["accion"] == settings.wompi_checkout_url
    campos = inicio["campos"]
    assert campos["public-key"] == "pub_test_xyz"
    assert campos["currency"] == "COP"
    assert campos["amount-in-cents"] == "1050000"  # total 10500.00 de payload_orden
    assert campos["reference"] == inicio["pago"]["referencia"]
    assert campos["integrity-sing"] == construir_firma_integridad(
        1050000, "COP", campos["reference"], "integ_test"
    )
    assert campos["redirect-url"] == f"{settings.app_public_url}/pedidos/{orden['id']}"

    estado = await cliente_autenticado.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    assert estado.status_code == 200
    data = estado.json()
    assert data["metodo"] == "wompi"
    assert data["orden_estado"] == "pendiente"
    assert data["pasarela_configurada"] is True
    assert data["pago"]["estado"] == "pendiente"
    assert data["pago"]["referencia"] == campos["reference"]
    assert estado.headers["cache-control"] == "no-store"


async def test_pagar_orden_ajena_da_403(fabrica_clientes, monkeypatch):
    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    crear_cliente = await fabrica_clientes
    dueno = await crear_cliente("dueno@test.local")
    intruso = await crear_cliente("intruso@test.local")

    orden = await _crear_orden(dueno)
    respuesta = await intruso.post(
        f"/api/v1/pagos/ordenes/{orden['id']}/iniciar", json={"metodo": "wompi"}
    )
    assert respuesta.status_code == 403


async def test_webhook_con_checksum_valido_aprueba(client, cliente_autenticado, monkeypatch):
    secreto = "evento_test"
    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    monkeypatch.setattr(settings, "wompi_events_secret", secreto)

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])
    referencia = inicio["pago"]["referencia"]

    evento = _firmar_evento(_evento_wompi(referencia, 1050000), secreto)
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["ok"] is True

    estado = await client.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    data = estado.json()
    assert data["pago"]["estado"] == "aprobado"
    assert data["pago"]["transaccion_id"] == "trans-123"
    assert data["orden_estado"] == "pagado"


async def test_webhook_con_checksum_invalido_da_401(client, cliente_autenticado, monkeypatch):
    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    monkeypatch.setattr(settings, "wompi_events_secret", "evento_test")

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])

    evento = _firmar_evento(_evento_wompi(inicio["pago"]["referencia"], 1050000), "otro-secreto")
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 401

    estado = await client.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    assert estado.json()["orden_estado"] == "pendiente"


async def test_webhook_aprueba_solo_si_la_api_lo_confirma(client, cliente_autenticado, monkeypatch):
    """Sin firma de eventos, la aprobacion exige verificacion server-to-server."""
    import app.pagos.router as router_pagos

    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    monkeypatch.setattr(settings, "wompi_events_secret", "")

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])
    referencia = inicio["pago"]["referencia"]

    evento = _evento_wompi(referencia, 1050000)

    async def _verificacion_aprobada(transaccion_id):
        return {"status": "APPROVED", "amount_in_cents": 1050000, "reference": referencia}

    monkeypatch.setattr(router_pagos, "consultar_transaccion", _verificacion_aprobada)
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 200
    estado = await client.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    assert estado.json()["orden_estado"] == "pagado"


async def test_webhook_no_aprueba_si_la_api_disiente(client, cliente_autenticado, monkeypatch):
    import app.pagos.router as router_pagos

    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    monkeypatch.setattr(settings, "wompi_events_secret", "")

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])

    async def _verificacion_declinada(transaccion_id):
        return {"status": "DECLINED", "amount_in_cents": 1050000, "reference": inicio["pago"]["referencia"]}

    monkeypatch.setattr(router_pagos, "consultar_transaccion", _verificacion_declinada)
    evento = _evento_wompi(inicio["pago"]["referencia"], 1050000, estado="APPROVED")
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 200

    estado = await client.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    data = estado.json()
    assert data["pago"]["estado"] == "pendiente"
    assert data["orden_estado"] == "pendiente"


async def test_webhook_rechaza_monto_adulterado(client, cliente_autenticado, monkeypatch):
    """Checksum valido pero monto distinto al registrado: no se aprueba."""
    secreto = "evento_test"
    monkeypatch.setattr(settings, "wompi_public_key", "pub_test_xyz")
    monkeypatch.setattr(settings, "wompi_integrity_secret", "integ_test")
    monkeypatch.setattr(settings, "wompi_events_secret", secreto)

    orden = await _crear_orden(cliente_autenticado)
    inicio = await _iniciar_pago(cliente_autenticado, orden["id"])

    evento = _firmar_evento(_evento_wompi(inicio["pago"]["referencia"], 100), secreto)  # 1 peso
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 200

    estado = await client.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    data = estado.json()
    assert data["pago"]["estado"] == "pendiente"
    assert data["orden_estado"] == "pendiente"


async def test_webhook_ignora_referencias_desconocidas(client, monkeypatch):
    monkeypatch.setattr(settings, "wompi_events_secret", "evento_test")
    evento = _firmar_evento(_evento_wompi("LEA-NOEXISTE-99", 1050000), "evento_test")
    respuesta = await client.post("/api/v1/pagos/webhook/wompi", json=evento)
    assert respuesta.status_code == 200
    assert "ignorado" in respuesta.json()["detalle"]


async def test_estado_pago_orden_contra_entrega(cliente_autenticado):
    cuerpo = payload_orden(metodo_pago="contra_entrega")
    respuesta = await cliente_autenticado.post("/api/v1/ordenes/", json=cuerpo)
    assert respuesta.status_code == 201
    orden = respuesta.json()

    estado = await cliente_autenticado.get(f"/api/v1/pagos/ordenes/{orden['id']}")
    assert estado.status_code == 200
    data = estado.json()
    assert data["metodo"] == "contra_entrega"
    assert data["pago"] is None
    assert data["pasarela_configurada"] is False


async def test_estado_pago_orden_inexistente_da_404(client):
    respuesta = await client.get(f"/api/v1/pagos/ordenes/{_uuid_aleatorio()}")
    assert respuesta.status_code == 404


def _uuid_aleatorio():
    import uuid

    return uuid.uuid4()
