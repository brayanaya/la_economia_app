import uuid
from decimal import Decimal

CAMPOS_PRIVADOS = {"cliente_telefono", "notas"}


def payload_orden(**cambios):
    base = {
        "sede_id": str(uuid.uuid4()),
        "cliente_nombre": "Cliente Prueba",
        "cliente_telefono": "3101234567",
        "notas": "Direccion: Calle 10 # 5-20, Neiva | Pago: Nequi",
        "items": [
            {
                "producto_id": "p-1",
                "nombre": "Leche Entera 1L",
                "cantidad": 2,
                "precio_unitario": 4500,
                "imagen_url": "/logo.png",
            },
            {"producto_id": "p-2", "nombre": "Pan Tajado", "cantidad": 1, "precio_unitario": 1500},
        ],
    }
    base.update(cambios)
    return base


async def crear(client, **cambios):
    respuesta = await client.post("/api/v1/ordenes/", json=payload_orden(**cambios))
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def test_consultar_orden_existente(client):
    creada = await crear(client)

    respuesta = await client.get(f"/api/v1/ordenes/{creada['id']}")

    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["id"] == creada["id"]
    assert data["sede_id"] == creada["sede_id"]
    assert data["estado"] == "pendiente"
    assert data["cliente_nombre"] == "Cliente Prueba"
    assert Decimal(data["total"]) == Decimal("10500.00")
    assert {i["nombre"] for i in data["items"]} == {"Leche Entera 1L", "Pan Tajado"}
    for item in data["items"]:
        assert set(item) == {"nombre", "imagen_url", "cantidad", "precio_unitario", "subtotal"}
    assert respuesta.headers["cache-control"] == "no-store"


async def test_respuesta_publica_no_expone_datos_personales(client):
    creada = await crear(client)

    respuesta = await client.get(f"/api/v1/ordenes/{creada['id']}")

    assert respuesta.status_code == 200
    assert CAMPOS_PRIVADOS.isdisjoint(respuesta.json().keys())
    assert "3101234567" not in respuesta.text
    assert "Calle 10" not in respuesta.text


async def test_orden_inexistente_devuelve_404(client):
    respuesta = await client.get(f"/api/v1/ordenes/{uuid.uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Pedido no encontrado"


async def test_id_con_formato_invalido_devuelve_422(client):
    respuesta = await client.get("/api/v1/ordenes/no-es-un-uuid")

    assert respuesta.status_code == 422


async def test_cada_orden_se_consulta_por_su_propio_id(client):
    a = await crear(client, cliente_nombre="Cliente A")
    b = await crear(client, cliente_nombre="Cliente B")

    ra = await client.get(f"/api/v1/ordenes/{a['id']}")
    rb = await client.get(f"/api/v1/ordenes/{b['id']}")

    assert ra.json()["cliente_nombre"] == "Cliente A"
    assert rb.json()["cliente_nombre"] == "Cliente B"
    assert ra.json()["id"] != rb.json()["id"]
