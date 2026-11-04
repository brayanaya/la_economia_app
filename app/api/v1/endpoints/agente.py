from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid
from decimal import Decimal

from app.core.config import settings
from app.core.database import get_db
from app.core.catalog_state import catalogo_state, get_catalogo_state
from app.schemas.agente import (
    AgenteChatRequest,
    AgenteChatResponse,
    PresupuestoItemResponse,
    PresupuestoResponse,
    ComparacionResponse,
    ComparacionItemResponse,
    CartActionAdd,
    CartActionRemove,
    CartActionUpdate,
    CartActionClear,
    CartActionList,
    CartActionItem,
    CartActionConfirmClear,
)
from app.schemas.comparison import (
    TipoComparacion,
    SolicitudComparacion,
)
from app.services.embeddings import get_embedding
from app.services.agente import generar_respuesta_agente, _detectar_intencion_general, _es_saludo, _es_despedida
from app.services.recetas import detectar_intencion_receta, obtener_receta_por_id
from app.services.providers import get_proveedor_catalogo, get_proveedor_registry
from app.services.providers.base import FiltrosBusqueda, TipoBusqueda
from app.services.budget_planner import (
    BudgetPlanner,
    crear_budget_planner,
    EstadoProductoPresupuesto,
    EstadoPresupuesto,
)
from app.services.comparison_engine import ComparisonEngine
from app.services.conversation import (
    get_conversation_memory,
    ContextoConversacion,
    MensajeConversacion,
    RolMensaje,
)

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgenteChatResponse,
    summary="Agente conversacional RAG: Aya - asistente experta de compras y cocina",
)
async def agente_chat(
    payload: AgenteChatRequest,
    db: AsyncSession = Depends(get_db),
    proveedor = Depends(get_proveedor_catalogo),
    registry = Depends(get_proveedor_registry),
    catalog_state = Depends(get_catalogo_state),
    memory = Depends(get_conversation_memory),
) -> AgenteChatResponse:
    """
    Flujo completo de Aya con Provider Pattern y Memoria Conversacional:
    1. Obtiene/crea contexto de conversación
    2. Detecta si el usuario pide una receta específica
    3. Busca productos usando el proveedor activo (Mock/MasControl)
    4. Genera respuesta conversacional con el prompt maestro de Aya + contexto
    5. Actualiza memoria conversacional
    6. Incluye estado del catálogo en la respuesta
    """
    # Verificar estado del catálogo
    estado_catalogo = catalog_state.obtener_estado_para_frontend()

    # 1. Obtener o crear contexto de conversación
    conversacion_id = payload.conversacion_id
    if not conversacion_id:
        # Generar nuevo ID si no viene del frontend
        conversacion_id = str(uuid.uuid4())

    # Obtener usuario_id si está autenticado (opcional)
    usuario_id = None
    # TODO: Obtener del auth context si hay sesión

    contexto = memory.obtener_o_crear(conversacion_id, usuario_id)

    # 2. Detectar intención de receta ANTES de buscar productos
    receta_id = detectar_intencion_receta(payload.mensaje)
    receta_detectada = receta_id if receta_id else None

    # 3. Detectar intención general para logging/contexto
    intencion_general = _detectar_intencion_general(payload.mensaje)

    # 4. Búsqueda de productos usando el proveedor activo
    # Determinar si necesitamos buscar productos
    es_saludo_o_despedida = _es_saludo(payload.mensaje) or _es_despedida(payload.mensaje)

    # Detectar si la consulta requiere precios/stock reales del catálogo
    # Palabras que indican necesidad EXPLÍCITA de consultar catálogo real (compra/precios)
    # NO incluir verbos de receta como "hacer", "preparar", "cocinar" que son consultas de knowledge base
    mensaje_lower = payload.mensaje.lower()
    necesita_catalogo_real = any(p in mensaje_lower for p in [
        # Precios y costos EXPLÍCITOS
        "precio", "cuanto cuesta", "cuánto cuesta", "costo", "cuestan", "vale", "valen",
        "presupuesto", "me alcanza", "con ", "mil pesos", "que me alcanza",
        # Comprar/agregar al carrito - ACCIONES DE COMPRA EXPLÍCITAS
        "comprar", "agrega ", "añade ", "lleva ", "pon ", "mete ",
        "lista de mercado", "lista de compras", "mercado para", "hacer el mercado",
        # Disponibilidad/stock
        "hay stock", "disponible", "tienen ", "tiene ", "queda ", "quedan ",
        # Recetas -> compra de ingredientes (PALABRAS DE COMPRA EXPLÍCITAS)
        "comprar para", "mercado para", "lista para",
        # Comparativas que necesitan productos reales
        "cual es mejor", "cuál es mejor", "que es mejor", "qué es mejor",
        "mejor opcion", "mejor opción", "comparar",
    ])

    # EXCEPCIONES: consultas de receta pura que NO deben buscar catálogo
    # "que puedo hacer", "se me antoja", "receta de", "como hacer", "como preparar"
    es_consulta_receta_pura = any(p in mensaje_lower for p in [
        "que puedo hacer", "qué puedo hacer",
        "se me antoja",
        "receta de", "receta para",
        "como hacer ", "cómo hacer ",
        "como preparar ", "cómo preparar ",
        "ingredientes de ", "ingredientes para ",
        "pasos de ", "pasos para ",
        "recomiendame algo para cocinar", "recomiéndame algo para cocinar",
        "recomiendame para cocinar", "recomiéndame para cocinar",
        "algo para cocinar", "algo para preparar",
        "ideas para cocinar", "ideas para preparar",
        "ideas para la cena", "ideas para el almuerzo", "ideas para desayuno",
        "ideas para la comida", "ideas para cenar", "ideas para almorzar",
    ]) and not any(p in mensaje_lower for p in [
        "comprar", "lista", "mercado", "precio", "cuanto", "cuánto", "presupuesto"
    ])

    # Detectar consulta de receta PURA (solo conocimiento culinario, no compra)
    # Si hay receta detectada Y no hay palabras de compra -> no buscar catálogo
    # O si es consulta de receta pura detectada por palabras clave
    es_receta_pura = (receta_detectada or es_consulta_receta_pura) and not necesita_catalogo_real

    # Consultas generales que no necesitan catálogo (FAQ, fuera_tema, consejos generales)
    es_consulta_general = intencion_general in ("fuera_tema", "faq") and not necesita_catalogo_real

    productos_relevantes = []
    hubo_resultados = False

    # Buscar en catálogo si:
    # - No es saludo/despedida
    # - No es receta pura (solo conocimiento)
    # - No es consulta general pura
    if not es_saludo_o_despedida and not es_receta_pura and not es_consulta_general:
        try:
            filtros = FiltrosBusqueda(
                sede_id=str(payload.sede_id) if payload.sede_id else None,
                solo_con_stock=True,
                limite=8,
                ordenar_por="relevancia"
            )
            # Usar búsqueda textual por ahora (semántica requiere embeddings del proveedor real)
            productos_encontrados = await proveedor.buscar(
                payload.mensaje,
                filtros=filtros,
                tipo_busqueda=TipoBusqueda.TEXTO
            )
            # Limitar a 4 más relevantes
            productos_relevantes = productos_encontrados[:4]
            hubo_resultados = len(productos_relevantes) > 0
        except Exception as e:
            # Log error but don't fail - agent can still respond conversationally
            import logging
            logging.getLogger(__name__).warning(f"Error buscando productos: {e}")
            productos_relevantes = []
            hubo_resultados = False

    # 5. DETECCIÓN DE INTENCIÓN DE PRESUPUESTO / LISTA DE MERCADO
    # Palabras clave que indican que el usuario quiere calcular presupuesto
    mensaje_lower = payload.mensaje.lower()
    es_consulta_presupuesto = any(p in mensaje_lower for p in [
        "presupuesto", "me alcanza", "con ", "mil pesos", "que me alcanza", "qué me alcanza",
        "lista de mercado", "lista de compras", "mercado para", "hacer el mercado",
        "calcular", "cuanto sale", "cuánto sale", "cuanto cuesta", "cuánto cuesta",
        "comparar precios", "mejor precio", "opcion mas barata", "opción más barata",
    ]) and not any(p in mensaje_lower for p in [
        "como hacer", "cómo hacer", "como preparar", "cómo preparar",
        "receta de", "receta para", "ingredientes de", "pasos de"
    ])

    # También detectar si hay lista explícita en el payload
    tiene_lista_explicita = payload.lista_mercado is not None and len(payload.lista_mercado) > 0
    tiene_presupuesto_explicito = payload.presupuesto is not None and payload.presupuesto > 0

    presupuesto_resultado = None

    # EJECUTAR PLANIFICADOR DE PRESUPUESTO si:
    # - Usuario pregunta explícitamente por presupuesto/lista de mercado
    # - O hay lista explícita en el payload
    # - O hay presupuesto explícito en el payload
    if es_consulta_presupuesto or tiene_lista_explicita or tiene_presupuesto_explicito:
        try:
            # Crear planner con el proveedor activo
            planner = crear_budget_planner(proveedor)

            # Determinar items a procesar
            items_para_calcular = []

            if tiene_lista_explicita:
                # Lista explícita del payload
                items_para_calcular = payload.lista_mercado
            elif tiene_presupuesto_explicito:
                # Solo hay presupuesto - necesitamos extraer productos del mensaje/contexto
                # Usar productos mencionados en la conversación reciente + búsqueda actual
                items_para_calcular = _extraer_items_para_presupuesto(
                    payload.mensaje,
                    productos_relevantes,
                    contexto
                )
            else:
                # Consulta de presupuesto sin lista explícita - extraer del mensaje/contexto
                items_para_calcular = _extraer_items_para_presupuesto(
                    payload.mensaje,
                    productos_relevantes,
                    contexto
                )

            if items_para_calcular:
                # Calcular presupuesto
                presupuesto_limite = Decimal(str(payload.presupuesto)) if payload.presupuesto else None
                sede_id_str = str(payload.sede_id) if payload.sede_id else None

                presupuesto_resultado_raw = await planner.calcular_presupuesto(
                    items_para_calcular,
                    presupuesto_limite=presupuesto_limite,
                    sede_id=sede_id_str
                )

                # Convertir a schema de respuesta
                presupuesto_resultado = _convertir_presupuesto_a_response(presupuesto_resultado_raw)

                # Guardar en contexto conversacional para futuras referencias
                contexto.presupuesto_actual = presupuesto_resultado_raw
                contexto.lista_mercado_actual = items_para_calcular

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error en planificador de presupuesto: {e}")
            presupuesto_resultado = None

    # 5B. DETECCIÓN DE INTENCIÓN DE COMPARACIÓN Y EJECUCIÓN DEL COMPARISON ENGINE
    # Detectar si el usuario quiere comparar productos
    mensaje_lower = payload.mensaje.lower()
    es_consulta_comparacion = any(p in mensaje_lower for p in [
        "cual es mejor", "cuál es mejor", "que es mejor", "qué es mejor",
        "cual recomiendas", "qué recomiendas", "que recomiendas",
        "comparar", "comparacion", "comparación",
        "diferencia", "mejor opcion", "mejor opción",
        "cual aceite", "qué aceite", "que aceite", "cuál aceite",
        "cual detergente", "qué detergente", "que detergente",
        "cual cafe", "qué cafe", "que café", "cuál café",
        "cual leche", "qué leche", "que leche", "cuál leche",
        "cual arroz", "qué arroz", "que arroz", "cuál arroz",
        "cual pan", "qué pan", "que pan", "cuál pan",
        "versus", "vs ", "mejor que", "peor que", "x vs", "contra ",
        "mejor cafe", "mejor café", "mejor aceite", "mejor detergente",
        "mejor leche", "mejor arroz", "mejor pan", "mejor queso",
        "mejor yogurt", "mejor jugo", "mejor cerveza",
        "que rinde mas", "qué rinde más", "que rinde más",
        "cual sale mas barato", "cuál sale más barato", "que sale mas barato",
    ])

    comparacion_resultado = None

    # Ejecutar Comparison Engine si hay intención de comparación
    if es_consulta_comparacion:
        try:
            # Crear motor de comparación con el proveedor activo
            comparison_engine = ComparisonEngine(proveedor)

            # Extraer términos de búsqueda del mensaje
            # Usar el mensaje completo como términos, o productos encontrados
            terminos_busqueda = []

            # Si hay productos ya encontrados, usar sus nombres/marcas
            if productos_relevantes:
                for p in productos_relevantes[:3]:
                    termino = f"{p.marca or ''} {p.nombre}".strip()
                    if termino and termino not in terminos_busqueda:
                        terminos_busqueda.append(termino)

            # Si no hay productos, extraer términos del mensaje
            if not terminos_busqueda:
                # Palabras clave de productos comunes en comparativas
                productos_comunes = [
                    "aceite", "café", "cafe", "leche", "arroz", "detergente",
                    "pan", "queso", "yogurt", "jugo", "cerveza", "shampoo",
                    "jabon", "jabón", "pasta", "fideos", "azucar", "azúcar",
                    "sal", "harina", "chocolate", "galletas", "atun", "atún",
                    "sardinas", "huevos", "huevo", "mantequilla", "margarina"
                ]
                for prod in productos_comunes:
                    if prod in mensaje_lower and prod not in terminos_busqueda:
                        terminos_busqueda.append(prod)

            # Asegurar al menos 2 términos (requerido por SolicitudComparacion)
            if len(terminos_busqueda) < 2:
                # Agregar términos genéricos basados en el primer término
                if terminos_busqueda:
                    base = terminos_busqueda[0]
                    if base in ["aceite", "café", "cafe", "leche", "arroz", "detergente"]:
                        # Buscar variaciones
                        variaciones = {
                            "aceite": ["girasol", "oliva", "maiz", "canola", "vegetal"],
                            "café": ["molido", "grano", "instantaneo", "descafeinado"],
                            "cafe": ["molido", "grano", "instantaneo", "descafeinado"],
                            "leche": ["entera", "semidescremada", "descremada", "en polvo"],
                            "arroz": ["blanco", "integral", "vaporizado", "grana larga"],
                            "detergente": ["liquido", "polvo", "pastillas", "cápsulas"],
                        }
                        for v in variaciones.get(base, [])[:3]:
                            if v not in terminos_busqueda:
                                terminos_busqueda.append(v)
                            if len(terminos_busqueda) >= 2:
                                break

            # Si aún no hay suficientes términos, usar búsqueda genérica
            if len(terminos_busqueda) < 2:
                terminos_busqueda = [mensaje_lower[:50], "producto"]

            # Determinar tipo de comparación basado en el mensaje
            tipo_comparacion = TipoComparacion.COMPLETA
            if any(p in mensaje_lower for p in ["precio", "barato", "cuesta", "vale", "economico", "económico"]):
                tipo_comparacion = TipoComparacion.PRECIO_POR_UNIDAD
            elif any(p in mensaje_lower for p in ["rinde", "cantidad", "mas producto", "más producto", "mas por", "más por"]):
                tipo_comparacion = TipoComparacion.CANTIDAD
            elif any(p in mensaje_lower for p in ["disponible", "stock", "hay ", "tienen "]):
                tipo_comparacion = TipoComparacion.DISPONIBILIDAD

            # Extraer contexto adicional
            contexto_adicional = None
            if "freir" in mensaje_lower or "frit" in mensaje_lower:
                contexto_adicional = "para freir"
            elif "ensalada" in mensaje_lower:
                contexto_adicional = "para ensalada"
            elif "hornear" in mensaje_lower or "postre" in mensaje_lower:
                contexto_adicional = "para hornear"

            # Crear solicitud de comparación
            solicitud = SolicitudComparacion(
                terminos_busqueda=terminos_busqueda[:5],  # Máximo 5 términos
                tipo_comparacion=tipo_comparacion,
                sede_id=str(payload.sede_id) if payload.sede_id else None,
                contexto_adicional=contexto_adicional,
            )

            # Ejecutar comparación
            comparacion_raw = await comparison_engine.comparar(solicitud, solicitud.sede_id)

            # Convertir a schema de respuesta del agente (ComparacionResponse de app.schemas.agente)
            comparacion_resultado = ComparacionResponse(
                tipo_comparacion=comparacion_raw.tipo_comparacion.value,
                criterio=comparacion_raw.criterio,
                productos=[
                    ComparacionItemResponse(
                        id=item.producto.id,
                        sku=item.producto.sku,
                        nombre=item.producto.nombre,
                        marca=item.producto.marca,
                        presentacion=item.producto.presentacion,
                        precio_final=item.producto.precio_final,
                        precio_por_unidad_base=item.producto.precio_por_unidad_base,
                        unidad_medida=item.producto.unidad_medida,
                        stock=item.producto.stock,
                        disponible=item.producto.disponible,
                        tiene_promocion=item.producto.tiene_promocion,
                        puntuacion=item.puntuacion,
                        razones=item.razones,
                    )
                    for item in comparacion_raw.productos
                ],
                mejor_opcion_id=comparacion_raw.mejor_opcion.id if comparacion_raw.mejor_opcion else None,
                explicacion=comparacion_raw.explicacion,
                limitaciones=comparacion_raw.limitaciones,
                sede_id=comparacion_raw.sede_id,
                comparables=comparacion_raw.comparables,
            )

            # Guardar en contexto conversacional para futuras referencias
            contexto.comparacion_actual = comparacion_raw

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error en comparison engine: {e}")
            comparacion_resultado = None

    # 5C. DETECCIÓN DE INTENCIÓN DE CARRITO Y GENERACIÓN DE ACCIONES ESTRUCTURADAS
    # El agente detecta intenciones de carrito y devuelve acciones estructuradas
    # El frontend ejecuta estas acciones usando el hook useCarrito existente
    cart_actions = _detectar_y_generar_acciones_carrito(
        mensaje=payload.mensaje,
        productos_relevantes=productos_relevantes,
        contexto=contexto,
        sede_id=str(payload.sede_id) if payload.sede_id else None,
    )

    # 6. Generar respuesta con Aya (incluye info de receta si se detectó)
    # Pasar historial conversacional al agente para contexto
    historial_llm = contexto.obtener_historial_para_llm(limite=8)

    # Preparar contexto de presupuesto para el LLM
    contexto_presupuesto = None
    if presupuesto_resultado:
        contexto_presupuesto = {
            "total": float(presupuesto_resultado.total_con_precio),
            "presupuesto_limite": float(presupuesto_resultado.presupuesto_limite) if presupuesto_resultado.presupuesto_limite else None,
            "excedido": presupuesto_resultado.presupuesto_excedido,
            "diferencia": float(presupuesto_resultado.diferencia_presupuesto),
            "items": [
                {
                    "termino": item.termino_busqueda,
                    "cantidad": item.cantidad,
                    "precio": item.precio_unitario,
                    "subtotal": item.subtotal,
                    "estado": item.estado,
                }
                for item in presupuesto_resultado.items
            ],
        }

    respuesta_texto, generado_por_llm = await generar_respuesta_agente(
        payload.mensaje,
        productos_relevantes,
        receta_detectada=receta_detectada,
        historial_conversacion=historial_llm,
        contexto_conversacion=contexto.obtener_contexto_resumido(),
        contexto_presupuesto=contexto_presupuesto,
        contexto_comparacion=comparacion_resultado,
    )

    # 6. Preparar datos de receta para el frontend (si aplica)
    # Usar receta detectada en este turno O receta del contexto conversacional
    receta_para_respuesta = receta_detectada or contexto.receta_actual
    receta_data = None
    if receta_para_respuesta:
        receta = obtener_receta_por_id(receta_para_respuesta)
        if receta:
            receta_data = {
                "id": receta.id,
                "nombre": receta.nombre,
                "descripcion": receta.descripcion,
                "categoria": receta.categoria,
                "tiempo_min": receta.tiempo_min,
                "porciones": receta.porciones,
                "costo_estimado_cop": receta.costo_estimado_cop,
                "imagen_url": receta.imagen_url,
                "ingredientes": [
                    {
                        "nombre": ing.nombre,
                        "cantidad": ing.cantidad,
                        "busqueda_catalogo": ing.busqueda_catalogo,
                        "obligatorio": ing.obligatorio,
                        "notas": ing.notas,
                    }
                    for ing in receta.ingredientes
                ],
                "pasos": receta.pasos,
                "tags": receta.tags,
            }

    # 7. Actualizar memoria conversacional
    # Extraer productos mencionados en la respuesta para contexto futuro
    productos_mencionados = [p.id for p in productos_relevantes] if productos_relevantes else []

    mensaje_usuario = MensajeConversacion(
        rol=RolMensaje.USUARIO,
        contenido=payload.mensaje,
        productos_mencionados=productos_mencionados,
        receta_id=receta_detectada,
        intencion=intencion_general,
    )

    mensaje_asistente = MensajeConversacion(
        rol=RolMensaje.ASISTENTE,
        contenido=respuesta_texto,
        productos_mencionados=productos_mencionados,
        receta_id=receta_detectada,
    )

    contexto.agregar_mensaje(mensaje_usuario)
    contexto.agregar_mensaje(mensaje_asistente)
    memory.guardar(contexto)

    # 8. Construir respuesta con estado de catálogo
    from app.schemas.agente import CatalogoEstadoResponse
    estado_response = CatalogoEstadoResponse(
        estado=estado_catalogo["estado"],
        conectado=estado_catalogo["conectado"],
        modo_mock=estado_catalogo["modo_mock"],
        ultimo_error=estado_catalogo.get("ultimo_error"),
        mensaje_usuario=estado_catalogo.get("mensaje_usuario", ""),
    )

    return AgenteChatResponse(
        mensaje=payload.mensaje,
        respuesta=respuesta_texto,
        productos_recomendados=productos_relevantes,
        hubo_resultados_relevantes=hubo_resultados,
        receta=receta_data,
        estado_catalogo=estado_response,
        conversacion_id=conversacion_id,
        generado_por_llm=generado_por_llm,
        presupuesto=presupuesto_resultado,
        comparacion=comparacion_resultado,
        cart_actions=cart_actions,
    )


# ==================== HELPER FUNCTIONS PARA PRESUPUESTO ====================

def _extraer_items_para_presupuesto(
    mensaje: str,
    productos_relevantes: List,
    contexto: ContextoConversacion
) -> List[Dict[str, Any]]:
    """
    Extrae items para cálculo de presupuesto desde:
    1. Productos encontrados en búsqueda actual
    2. Lista de mercado en contexto conversacional
    3. Productos recientes en contexto
    """
    items = []
    terminos_ya_agregados = set()

    # 1. Productos de la búsqueda actual (más relevantes)
    for p in productos_relevantes[:5]:
        termino = getattr(p, 'nombre', '') or getattr(p, 'descripcion', '') or str(p.id)
        termino_lower = termino.lower()
        if termino_lower not in terminos_ya_agregados:
            items.append({
                "termino_busqueda": termino,
                "cantidad": 1,
                "unidad": "unidad"
            })
            terminos_ya_agregados.add(termino_lower)

    # 2. Lista de mercado del contexto conversacional
    if contexto.lista_mercado_actual:
        for item in contexto.lista_mercado_actual:
            termino = item.get("termino_busqueda", "")
            if termino and termino.lower() not in terminos_ya_agregados:
                items.append({
                    "termino_busqueda": termino,
                    "cantidad": item.get("cantidad", 1),
                    "unidad": item.get("unidad", "unidad")
                })
                terminos_ya_agregados.add(termino.lower())

    # 3. Productos recientes del contexto
    for prod_id in contexto.productos_recientes[:5]:
        # No tenemos el nombre aquí, pero el planner buscará por ID si lo pasamos
        # Por ahora solo usamos términos de búsqueda
        pass

    # 4. Si no hay nada, intentar extraer del mensaje (heurística simple)
    if not items:
        # Palabras clave de productos comunes en el mensaje
        productos_comunes = [
            "arroz", "leche", "huevos", "pan", "carne", "pollo", "pescado",
            "papa", "tomate", "cebolla", "ajo", "aceite", "sal", "azucar", "azúcar",
            "cafe", "café", "chocolate", "galletas", "yogur", "queso", "mantequilla",
            "harina", "pasta", "fideos", "lentejas", "frijoles", "caraotas",
            "platano", "plátano", "mango", "papaya", "piña", "manzana", "pera"
        ]
        mensaje_lower = mensaje.lower()
        for prod in productos_comunes:
            if prod in mensaje_lower and prod not in terminos_ya_agregados:
                items.append({
                    "termino_busqueda": prod,
                    "cantidad": 1,
                    "unidad": "unidad"
                })
                terminos_ya_agregados.add(prod)

    return items


def _convertir_presupuesto_a_response(presupuesto_raw) -> PresupuestoResponse:
    """Convierte el resultado interno del planner al schema de respuesta."""
    items_response = []
    for item in presupuesto_raw.items:
        items_response.append(PresupuestoItemResponse(
            termino_busqueda=item.termino_busqueda,
            cantidad=item.cantidad,
            unidad=item.unidad,
            producto_id=str(item.producto.id) if item.producto else None,
            producto_nombre=item.producto.nombre if item.producto else None,
            precio_unitario=float(item.precio_unitario) if item.precio_unitario else 0,
            subtotal=float(item.subtotal) if item.subtotal else 0,
            estado=item.estado.value if hasattr(item.estado, 'value') else str(item.estado),
            mensaje=item.mensaje or "",
        ))

    return PresupuestoResponse(
        items=items_response,
        presupuesto_limite=float(presupuesto_raw.presupuesto_limite) if presupuesto_raw.presupuesto_limite else None,
        total_con_precio=float(presupuesto_raw.total_con_precio),
        total_sin_precio=presupuesto_raw.total_sin_precio,
        total_no_encontrados=presupuesto_raw.total_no_encontrados,
        total_sin_stock=presupuesto_raw.total_sin_stock,
        estado=presupuesto_raw.estado.value if hasattr(presupuesto_raw.estado, 'value') else str(presupuesto_raw.estado),
        mensaje=presupuesto_raw.mensaje or "",
        presupuesto_excedido=presupuesto_raw.presupuesto_excedido,
        diferencia_presupuesto=float(presupuesto_raw.diferencia_presupuesto),
        sede_id=presupuesto_raw.sede_id,
        catalogo_conectado=presupuesto_raw.catalogo_conectado,
        proveedor_usado=presupuesto_raw.proveedor_usado,
        resumen_usuario=presupuesto_raw.resumen_usuario,
    )


# ==================== HELPER FUNCTIONS PARA ACCIONES DE CARRITO ====================

def _normalizar_texto_carrito(texto: str) -> str:
    """Normaliza texto para detección de intenciones de carrito."""
    import re
    import unicodedata
    # Expandir abreviaciones colombianas comunes
    abreviaciones = {
        r"\bxq\b": "porque",
        r"\bq\b(?=\s|$)": "que",
        r"\bk\b(?=\s|$)": "que",
        r"\bpa\b(?=\s|$)": "para",
        r"\bpaa\b(?=\s|$)": "para",
        r"\bta\b(?=\s|$)": "esta",
        r"\btas\b(?=\s|$)": "estas",
        r"\btoy\b(?=\s|$)": "estoy",
        r"\bvoy\b(?=\s|$)": "voy",
        r"\bweno\b": "bueno",
        r"\bwena\b": "buena",
        r"\bkn\b": "con",
        r"\bkiero\b": "quiero",
        r"\bkere\b": "quiere",
    }
    texto_expandido = texto.lower()
    for patron, expansion in abreviaciones.items():
        texto_expandido = re.sub(patron, expansion, texto_expandido)

    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto_expandido)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9 ]", "", sin_tildes).strip()


def _detectar_intencion_carrito(mensaje: str) -> Optional[str]:
    """Detecta la intención relacionada con el carrito."""
    m = _normalizar_texto_carrito(mensaje)

    # Agregar al carrito
    if any(p in m for p in [
        "agrega", "anade", "añade", "lleva", "pon ", "mete ",
        "agregar", "anadir", "añadir", "llevar", "poner", "meter",
        "quiero ", "quiero comprar", "comprar ", "agrego", "anado", "añado",
        "dame ", "dame dos", "dame tres", "dame un", "dame una",
        "ponme ", "ponme dos", "ponme tres", "ponme un", "ponme una",
        "echame ", "echame dos", "echame tres", "echame un", "echame una",
        "agrega dos", "agrega tres", "agrega un", "agrega una",
        "anade dos", "anade tres", "añade dos", "añade tres",
        "lleva dos", "lleva tres", "lleva un", "lleva una",
    ]):
        return "add"

    # Quitar del carrito
    if any(p in m for p in [
        "quita ", "quita el", "quita la", "quita los", "quita las",
        "quitar ", "quitar el", "quitar la", "quitar los", "quitar las",
        "elimina ", "elimina el", "elimina la", "elimina los", "elimina las",
        "eliminar ", "eliminar el", "eliminar la", "eliminar los", "eliminar las",
        "borra ", "borra el", "borra la", "borra los", "borra las",
        "borrar ", "borrar el", "borrar la", "borrar los", "borrar las",
        "saca ", "saca el", "saca la", "saca los", "saca las",
        "sacar ", "sacar el", "sacar la", "sacar los", "sacar las",
        "quita dos", "quita tres", "quita un", "quita una",
        "elimina dos", "elimina tres", "borra dos", "borra tres",
    ]):
        return "remove"

    # Actualizar cantidad en carrito
    if any(p in m for p in [
        "cambia ", "cambia el", "cambia la", "cambia los", "cambia las",
        "cambiar ", "cambiar el", "cambiar la", "cambiar los", "cambiar las",
        "modifica ", "modifica el", "modifica la", "modifica los", "modifica las",
        "modificar ", "modificar el", "modificar la", "modificar los", "modificar las",
        "actualiza ", "actualiza el", "actualiza la", "actualiza los", "actualiza las",
        "ponle ", "ponle dos", "ponle tres", "ponle un", "ponle una",
        "cambia por ", "cambialo por ", "cambiala por ",
    ]):
        return "update"

    # Vaciar carrito
    if any(p in m for p in [
        "vaciar carrito", "vaciar el carrito", "limpiar carrito", "limpiar el carrito",
        "borrar carrito", "borrar todo el carrito", "vaciar todo",
        "quita todo", "quita todos", "elimina todo", "elimina todos",
        "borra todo", "borra todos", "saca todo", "saca todos",
    ]):
        return "clear"

    # Listar/ver carrito
    if any(p in m for p in [
        "que tengo en el carrito", "qué tengo en el carrito",
        "que hay en el carrito", "qué hay en el carrito",
        "ver carrito", "mostrar carrito", "mi carrito",
        "cuanto llevo", "cuánto llevo", "total carrito", "total del carrito",
        "resumen carrito", "resumen del carrito", "lista carrito", "lista del carrito",
    ]):
        return "list"

    return None


def _extraer_cantidad(texto: str, default: int = 1) -> int:
    """Extrae cantidad numérica del texto (números o palabras)."""
    import re
    # Buscar números
    nums = re.findall(r'\b(\d+)\b', texto)
    if nums:
        return min(int(nums[0]), 99)

    # Buscar palabras de cantidad
    cantidades_palabras = {
        "un": 1, "una": 1, "uno": 1,
        "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "media": 0.5, "mitad": 0.5,
    }
    for palabra, valor in cantidades_palabras.items():
        if f" {palabra} " in f" {texto} " or texto.startswith(f"{palabra} ") or texto.endswith(f" {palabra}"):
            return int(valor) if valor >= 1 else 1

    return default


def _extraer_productos_con_cantidades(
    mensaje: str,
    productos_comunes: List[str],
    productos_relevantes: List,
    contexto: Optional[ContextoConversacion] = None
) -> List[tuple[str, int]]:
    """
    Extrae productos mencionados en el mensaje con sus cantidades individuales.
    Soporta: "agrega 2 leches y 3 panes", "lleva 1 arroz, 2 azúcar y 5 huevos"
    También usa contexto conversacional para referencias como "la leche de antes", "el pan".
    Retorna lista de tuplas (termino_producto, cantidad).
    """
    mensaje_norm = _normalizar_para_matching(mensaje)

    # Normalizar productos_comunes para que coincidan con el mensaje normalizado
    productos_comunes_norm = [_normalizar_para_matching(p) for p in productos_comunes]
    # Mapear normalizado -> original para retornar el término original
    norm_a_original = dict(zip(productos_comunes_norm, productos_comunes))

    # Patrones para extraer producto + cantidad
    # Ejemplos: "2 leches", "tres panes", "1 kg de arroz", etc.
    import re

    # Primero buscar patrones explícitos: cantidad + producto
    # "2 leches", "tres panes", "1 kg de arroz", etc.
    # Usar productos normalizados en el patrón
    patron_cantidad_producto = r'(\d+|un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+(?:de\s+)?(' + '|'.join(re.escape(p) for p in sorted(productos_comunes_norm, key=len, reverse=True)) + r')'

    matches = re.findall(patron_cantidad_producto, mensaje_norm)
    productos_con_cant = []

    for cantidad_str, producto_norm in matches:
        # Convertir cantidad
        cantidades_palabras = {
            "un": 1, "una": 1, "uno": 1,
            "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
            "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        }
        cantidad = cantidades_palabras.get(cantidad_str, int(cantidad_str) if cantidad_str.isdigit() else 1)
        cantidad = min(max(cantidad, 1), 99)
        # Retornar el término original
        producto_original = norm_a_original.get(producto_norm, producto_norm)
        productos_con_cant.append((producto_original, cantidad))

    # Si no se encontraron patrones explícitos, usar matching simple pero con cantidad global
    if not productos_con_cant:
        terminos_encontrados = _extraer_productos_mensaje(mensaje, productos_comunes)
        if terminos_encontrados:
            cantidad_global = _extraer_cantidad(mensaje_norm)
            productos_con_cant = [(t, cantidad_global) for t in terminos_encontrados]
        # Si tampoco hay términos y hay productos relevantes, usar los de la búsqueda
        elif productos_relevantes:
            for p in productos_relevantes[:3]:
                termino = (p.nombre or "").lower()
                if termino:
                    cantidad_global = _extraer_cantidad(mensaje_norm)
                    productos_con_cant.append((termino, cantidad_global))
        # Si aún no hay productos, buscar referencias en contexto conversacional
        elif contexto and contexto.productos_recientes:
            # Referencias como "la leche", "el pan", "esos", "los de antes"
            for prod_id in contexto.productos_recientes[:5]:
                # Buscar el producto en productos_relevantes por ID
                for p in productos_relevantes:
                    if str(getattr(p, 'id', '')) == str(prod_id):
                        termino = (p.nombre or "").lower()
                        if termino:
                            cantidad_global = _extraer_cantidad(mensaje_norm)
                            productos_con_cant.append((termino, cantidad_global))
                        break

    return productos_con_cant


def _buscar_producto_verificado(
    termino: str,
    productos_relevantes: List,
    contexto: ContextoConversacion,
    sede_id: Optional[str]
) -> Optional[object]:
    """
    Busca un producto verificado en el catálogo actual.
    Solo retorna productos que existan en productos_relevantes (búsqueda real del proveedor).
    NO crea productos ficticios.
    """
    termino_lower = termino.lower()
    termino_palabras = set(termino_lower.split())

    # 1. Buscar en productos relevantes de la búsqueda actual (productos reales del catálogo)
    for p in productos_relevantes:
        nombre_lower = (p.nombre or "").lower()
        marca_lower = (p.marca or "").lower()
        presentacion_lower = (p.presentacion or "").lower()
        sku_lower = (p.sku or "").lower()

        nombre_palabras = set(nombre_lower.split())
        marca_palabras = set(marca_lower.split()) if marca_lower else set()
        presentacion_palabras = set(presentacion_lower.split()) if presentacion_lower else set()

        # Matching exacto o por palabras completas (todas las palabras del término deben estar)
        if (termino_lower == nombre_lower or
            termino_lower == marca_lower or
            termino_lower == sku_lower or
            termino_lower == presentacion_lower or
            termino_palabras.issubset(nombre_palabras) or
            termino_palabras.issubset(marca_palabras) or
            termino_palabras.issubset(presentacion_palabras)):
            return p

    # 2. Buscar en productos recientes del contexto usando búsqueda en catálogo actual
    # Si el contexto tiene productos_recientes, buscar por ID en productos_relevantes
    for prod_id in contexto.productos_recientes:
        for p in productos_relevantes:
            if str(getattr(p, 'id', '')) == str(prod_id):
                return p

    # 3. NO buscar en lista_mercado_actual - esa lista puede tener términos no verificados

    return None


import re
import unicodedata
from typing import Set


def _normalizar_para_matching(texto: str) -> str:
    """Normaliza texto para matching exacto de palabras (sin tildes, solo alfanumérico y espacios)."""
    # Expandir abreviaciones colombianas comunes
    abreviaciones = {
        r"\bxq\b": "porque",
        r"\bq\b(?=\s|$)": "que",
        r"\bk\b(?=\s|$)": "que",
        r"\bpa\b(?=\s|$)": "para",
        r"\bpaa\b(?=\s|$)": "para",
        r"\bta\b(?=\s|$)": "esta",
        r"\btas\b(?=\s|$)": "estas",
        r"\btoy\b(?=\s|$)": "estoy",
        r"\bvoy\b(?=\s|$)": "voy",
        r"\bweno\b": "bueno",
        r"\bwena\b": "buena",
        r"\bkn\b": "con",
        r"\bkiero\b": "quiero",
        r"\bkere\b": "quiere",
    }
    texto_expandido = texto.lower()
    for patron, expansion in abreviaciones.items():
        texto_expandido = re.sub(patron, expansion, texto_expandido)

    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto_expandido)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9 ]", " ", sin_tildes).strip()


def _extraer_productos_mensaje(mensaje: str, productos_comunes: List[str]) -> List[str]:
    """
    Extrae productos mencionados en el mensaje usando matching de palabras completas.
    Evita coincidencias por subcadenas (ej: 'pan' no coincide con 'panela').
    """
    mensaje_norm = _normalizar_para_matching(mensaje)
    palabras_mensaje = set(mensaje_norm.split())

    terminos_encontrados = []
    for prod in productos_comunes:
        prod_norm = _normalizar_para_matching(prod)
        # Verificar que todas las palabras del producto estén en el mensaje
        prod_palabras = set(prod_norm.split())
        if prod_palabras.issubset(palabras_mensaje) and prod not in terminos_encontrados:
            terminos_encontrados.append(prod)

    return terminos_encontrados


def _buscar_producto_verificado(
    termino: str,
    productos_relevantes: List,
    contexto: ContextoConversacion,
    sede_id: Optional[str]
) -> Optional[object]:
    """
    Busca un producto verificado en el catálogo actual.
    Solo retorna productos que existan en productos_relevantes (búsqueda real del proveedor).
    NO crea productos ficticios.
    """
    termino_lower = termino.lower()
    termino_palabras = set(termino_lower.split())

    # 1. Buscar en productos relevantes de la búsqueda actual (productos reales del catálogo)
    for p in productos_relevantes:
        nombre_lower = (p.nombre or "").lower()
        marca_lower = (p.marca or "").lower()
        presentacion_lower = (p.presentacion or "").lower()
        sku_lower = (p.sku or "").lower()

        nombre_palabras = set(nombre_lower.split())
        marca_palabras = set(marca_lower.split()) if marca_lower else set()
        presentacion_palabras = set(presentacion_lower.split()) if presentacion_lower else set()

        # Matching exacto o por palabras completas (todas las palabras del término deben estar)
        if (termino_lower == nombre_lower or
            termino_lower == marca_lower or
            termino_lower == sku_lower or
            termino_lower == presentacion_lower or
            termino_palabras.issubset(nombre_palabras) or
            termino_palabras.issubset(marca_palabras) or
            termino_palabras.issubset(presentacion_palabras)):
            return p

    # 2. Buscar en productos recientes del contexto (solo si tenemos el objeto completo)
    # Nota: contexto.productos_recientes solo tiene IDs, no objetos completos

    # 3. NO buscar en lista_mercado_actual - esa lista puede tener términos no verificados

    return None


def _buscar_todos_productos_verificados(
    termino: str,
    productos_relevantes: List,
    contexto: ContextoConversacion,
    sede_id: Optional[str]
) -> List[object]:
    """Busca TODOS los productos que coincidan con el término (para detectar ambigüedad)."""
    termino_lower = termino.lower()
    termino_palabras = set(termino_lower.split())
    coincidencias = []

    for p in productos_relevantes:
        nombre_lower = (p.nombre or "").lower()
        marca_lower = (p.marca or "").lower()
        presentacion_lower = (p.presentacion or "").lower()
        sku_lower = (p.sku or "").lower()

        nombre_palabras = set(nombre_lower.split())
        marca_palabras = set(marca_lower.split()) if marca_lower else set()
        presentacion_palabras = set(presentacion_lower.split()) if presentacion_lower else set()

        # Matching exacto o por palabras completas
        if (termino_lower == nombre_lower or
            termino_lower == marca_lower or
            termino_lower == sku_lower or
            termino_lower == presentacion_lower or
            termino_palabras.issubset(nombre_palabras) or
            termino_palabras.issubset(marca_palabras) or
            termino_palabras.issubset(presentacion_palabras)):
            coincidencias.append(p)

    # También buscar en productos recientes del contexto
    for prod_id in contexto.productos_recientes:
        for p in productos_relevantes:
            if str(getattr(p, 'id', '')) == str(prod_id) and p not in coincidencias:
                coincidencias.append(p)

    return coincidencias


def _detectar_y_generar_acciones_carrito(
    mensaje: str,
    productos_relevantes: List,
    contexto: ContextoConversacion,
    sede_id: Optional[str]
) -> List:
    """Detecta intención de carrito y genera acciones estructuradas SOLO para productos verificados."""
    from app.schemas.agente import (
        CartActionAdd, CartActionRemove, CartActionUpdate,
        CartActionClear, CartActionList, CartActionItem,
        CartActionConfirmClear
    )

    intencion = _detectar_intencion_carrito(mensaje)
    if not intencion:
        return []

    mensaje_lower = mensaje.lower()
    acciones = []

    # Si no hay sede, no podemos hacer acciones que la requieran (add, remove, update)
    # Pero sí podemos listar y solicitar confirmación de clear
    if intencion in ("add", "remove", "update") and not sede_id:
        # Devolver acción especial indicando que falta sede
        return []

    # Lista de productos comunes - ordenados por longitud descendente para priorizar matches más específicos
    productos_comunes = [
        "papel higiénico", "papel higienico", "leche condensada", "crema de leche",
        "azúcar morena", "azucar morena", "queso costeño", "queso campesino",
        "queso americano", "cebolla larga", "cebolla junca", "almojábana", "almojabana",
        "chicharrón", "chicharron", "pimentón", "pimenton", "brócoli", "brocoli",
        "calabacín", "calabacin", "orégano", "oregano", "ají", "aji", "guascas", "guasca",
        "arroz", "leche", "huevos", "pan", "carne", "pollo", "pescado",
        "papa", "tomate", "cebolla", "ajo", "aceite", "sal", "azúcar", "azucar",
        "café", "cafe", "chocolate", "galletas", "yogur", "queso", "mantequilla",
        "harina", "pasta", "fideos", "lentejas", "frijoles", "caraotas",
        "plátano", "platano", "mango", "papaya", "piña", "manzana", "pera",
        "detergente", "jabón", "jabon", "shampoo", "pasta dental", "cepillo",
        "servilleta", "cerveza", "gaseosa", "jugo", "agua", "vino",
        "aguacate", "hass", "banano", "banana", "guineo",
        "arepa", "pandebono", "buñuelo", "buñuelo",
        "chorizo", "morcilla", "longaniza",
        "hamburguesa", "salchicha", "tocineta", "tocino",
        "margarina", "maicena", "almidón", "almidon", "panela",
        "comino", "color", "achiote", "pimienta",
        "laurel", "canela", "clavo", "cilantro",
        "zanahoria", "apio", "pepino", "lechuga", "espinaca", "acelga",
        "coliflor", "berenjena", "pimiento", "chile",
    ]

    try:
        if intencion == "add":
            # Extraer productos con cantidades individuales usando matching de palabras completas
            productos_con_cantidades = _extraer_productos_con_cantidades(mensaje, productos_comunes, productos_relevantes, contexto)

            # Generar items SOLO para productos verificados en el catálogo
            items_carrito = []

            for termino, cantidad in productos_con_cantidades[:5]:  # Máximo 5 productos por acción
                # Buscar TODOS los productos que coincidan para detectar ambigüedad
                coincidencias = _buscar_todos_productos_verificados(termino, productos_relevantes, contexto, sede_id)

                # Si hay ambigüedad (más de un producto coincide), NO agregamos (fix issue #6)
                if len(coincidencias) > 1:
                    continue  # Saltar producto ambiguo

                # Si hay exactamente una coincidencia, usarla
                if len(coincidencias) == 1:
                    producto = coincidencias[0]
                    items_carrito.append(CartActionItem(
                        producto_id=str(getattr(producto, 'id', termino)),
                        nombre=getattr(producto, 'nombre', termino),
                        cantidad=cantidad,
                        precio_unitario=float(getattr(producto, 'precio_final', 0) or 0),
                        sede_id=sede_id,
                        imagen_url=getattr(producto, 'imagen_url', None),
                    ))
                # Si no hay coincidencias, no agregamos (producto no verificado)

            if items_carrito:
                acciones.append(CartActionAdd(tipo="add", items=items_carrito))
            # Si no hay items verificados, no devolvemos acción (el agente responderá conversacionalmente)

        elif intencion == "remove":
            # Extraer productos mencionados usando matching de palabras completas
            terminos_encontrados = _extraer_productos_mensaje(mensaje, productos_comunes)

            producto_ids = []
            for termino in terminos_encontrados:
                # Buscar TODOS los productos que coincidan para detectar ambigüedad
                coincidencias = _buscar_todos_productos_verificados(termino, productos_relevantes, contexto, sede_id)

                # Si hay ambigüedad (más de un producto coincide), NO quitamos
                if len(coincidencias) > 1:
                    continue  # Saltar producto ambiguo

                # Si hay exactamente una coincidencia, usarla
                if len(coincidencias) == 1:
                    producto = coincidencias[0]
                    producto_ids.append(str(getattr(producto, 'id', termino)))

            if producto_ids:
                acciones.append(CartActionRemove(tipo="remove", producto_ids=producto_ids, sede_id=sede_id))

        elif intencion == "update":
            # Actualizar cantidad - solo para productos verificados
            # Usar extracción individual para soportar "cambia 2 leches y 3 panes"
            productos_con_cantidades = _extraer_productos_con_cantidades(mensaje, productos_comunes, productos_relevantes, contexto)

            items_carrito = []
            for termino, cantidad in productos_con_cantidades:
                # Buscar TODOS los productos que coincidan para detectar ambigüedad
                coincidencias = _buscar_todos_productos_verificados(termino, productos_relevantes, contexto, sede_id)

                # Si hay ambigüedad (más de un producto coincide), NO actualizamos
                if len(coincidencias) > 1:
                    continue  # Saltar producto ambiguo

                # Si hay exactamente una coincidencia, usarla
                if len(coincidencias) == 1:
                    producto = coincidencias[0]
                    items_carrito.append(CartActionItem(
                        producto_id=str(getattr(producto, 'id', termino)),
                        nombre=getattr(producto, 'nombre', termino),
                        cantidad=cantidad,
                        precio_unitario=float(getattr(producto, 'precio_final', 0) or 0),
                        sede_id=sede_id,
                        imagen_url=getattr(producto, 'imagen_url', None),
                    ))

            if items_carrito:
                acciones.append(CartActionUpdate(tipo="update", items=items_carrito))

        elif intencion == "clear":
            # Acción clear requiere confirmación explícita (fix issue #3)
            # Devolvemos una acción especial que el frontend debe confirmar
            acciones.append(CartActionConfirmClear(tipo="confirm_clear", sede_id=sede_id))

        elif intencion == "list":
            # Acción list debe devolver contenido real del carrito (fix issue #7)
            # El frontend ya tiene el carrito en contexto, pero devolvemos la acción
            # para que el agente pueda mencionar el contenido en su respuesta
            acciones.append(CartActionList(tipo="list", sede_id=sede_id))

    except Exception as e:
        # Log del error para debugging (fix issue #5 - no más except Exception: pass)
        import logging
        logging.getLogger(__name__).warning(f"Error generando acciones de carrito: {e}")
        # No devolvemos acciones en caso de error

    return acciones


@router.get(
    "/estado-catalogo",
    summary="Obtiene el estado actual del catálogo (conectado/desconectado)"
)
async def estado_catalogo(
    catalog_state = Depends(get_catalogo_state),
    registry = Depends(get_proveedor_registry),
):
    """Endpoint para que el frontend consulte el estado del catálogo."""
    info = registry.obtener_info_estado()
    return info


@router.delete(
    "/conversacion/{conversacion_id}",
    summary="Elimina una conversación (derecho al olvido - Ley 1581)"
)
async def eliminar_conversacion(
    conversacion_id: str,
    memory = Depends(get_conversation_memory),
):
    """Elimina el historial de una conversación."""
    eliminado = memory.eliminar(conversacion_id)
    if not eliminado:
        raise HTTPException(404, "Conversación no encontrada")
    return {"ok": True, "mensaje": "Conversación eliminada"}