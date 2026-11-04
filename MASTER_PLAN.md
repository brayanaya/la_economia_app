# PLAN MAESTRO: EVOLUCIÓN INTEGRAL DE LA ECONOMÍA AYA
# Estado: CATÁLOGO NO CONECTADO (MasControl pendiente) → ARQUITECTURA DUAL

## ANÁLISIS DE ESTADO ACTUAL

### ✅ YA IMPLEMENTADO Y FUNCIONAL
1. **Backend FastAPI** con arquitectura modular (app/, api/v1/, services/, models/, schemas/)
2. **Agente IA "Aya"** con:
   - Prompt maestro colombiano extenso (1000+ líneas)
   - Fuzzy matching para saludos/despedidas/abreviaciones
   - Few-shot examples (70+ casos reales)
   - Fallback determinista cuando LLM falla
   - Detección de intención de recetas (13 recetas colombianas)
   - Búsqueda semántica con pgvector/Ollama
   - Filtro híbrido stock/sede
3. **Recetas colombianas** (13 completas con ingredientes mapeados a catálogo)
4. **Frontend Next.js** con:
   - ChatAgente.tsx (modal recetas, grid ingredientes, add-all-to-cart, pasos)
   - Buscador semántico
   - Carrito multi-sede
   - Checkout contra entrega / Bre-B
5. **Autenticación** completa:
   - Registro/Login con Argon2
   - Google OAuth (ID token verification - requiere configuración)
   - Magic Links (passwordless)
   - TOTP/Google Authenticator (QR, verificación, códigos recuperación)
   - Consentimiento Ley 1581
6. **Pagos Wompi** (Web Checkout + Webhook seguro con verificación server-to-server)
7. **Tests** pytest (agente, pagos, órdenes)
8. **Docker Compose** + Alembic + Seed data (85 productos colombianos reales)

### ⚠️ PROBLEMAS CRÍTICOS IDENTIFICADOS
1. **Catálogo FICTICIO** - 85 productos seed NO son el catálogo real de MasControl
2. **LLM no responde** - `generar_texto` usa fallback determinista siempre (Ollama no corriendo / Anthropic sin API key)
3. **Google OAuth incompleto** - `verify_google_id_token` usa `jwt.decode(verify_signature=False)` - INSEGURO
4. **Wompi sin credenciales** - `wompi_configurada` = False (sin public key / integrity secret)
5. **Embeddings no generados** - `scripts_ingesta_catalogo` no ejecutado sobre BD real
6. **Arquitectura acoplada a catálogo seed** - El agente asume que productos en contexto = catálogo real

---

## ARQUITECTURA OBJETIVO: ESTADO DUAL (CATÁLOGO CONECTADO / NO CONECTADO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAYER: ASISTENTE IA (AGNÓSTICO A DATOS)             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  NLU Engine     │  │  Dialog Manager │  │  Response Generator         │ │
│  │  - Intent detection    │  - Context memory    │  - Persona "Aya"          │ │
│  │  - Entity extraction   │  - Slot filling      │  - Few-shot prompting     │ │
│  │  - Colombian NLP       │  - State tracking    │  - Deterministic fallback │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘ │
│           │                    │                       │                  │
│           └────────────────────┼───────────────────────┘                  │
│                                ▼                                          │
│                    ┌───────────────────────┐                              │
│                    │   TOOL REGISTRY       │                              │
│                    │  (Interface Contract) │                              │
│                    └───────────┬───────────┘                              │
└────────────────────────────────┼──────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  PROVIDER A   │      │  PROVIDER B     │      │  PROVIDER C     │
│  MOCK/FIXTURE │      │  MASCONTROL     │      │  FUTURE APIs    │
│  (Desarrollo) │      │  (Producción)   │      │  (Extensible)   │
└───────────────┘      └─────────────────┘      └─────────────────┘
```

### CONTRATO DE INTERFAZ (ProductProvider)
```python
class ProductProvider(Protocol):
    async def buscar(self, query: str, filtros: FiltrosBusqueda) -> list[Producto]
    async def obtener_por_id(self, id: str) -> Producto | None
    async def comparar(self, criterio: ComparacionCriterio) -> ComparacionResultado
    async def obtener_promociones(self, sede_id: str) -> list[Promocion]
    async def obtener_mas_vendidos(self, periodo: Periodo, limite: int) -> list[Producto]
    async def verificar_stock(self, producto_id: str, sede_id: str) -> StockInfo
    # ... más métodos
```

---

## FASES DE IMPLEMENTACIÓN

### FASE 1: FUNDACIÓN - Provider Pattern + Estado Dual (CRÍTICO - INMEDIATO)
**Objetivo**: Desacoplar IA del catálogo, implementar MockProvider y flag de estado

1. **Crear `app/core/catalog_state.py`** - Gestión de estado catálogo (conectado/no conectado)
2. **Crear `app/services/providers/base.py`** - Interface `ProductProvider` (Protocol)
3. **Crear `app/services/providers/mock_provider.py`** - MockProvider con fixtures realistas
4. **Crear `app/services/providers/mascontrol_provider.py`** - Esqueleto para MasControl (sin implementar)
5. **Refactorizar `app/services/agente.py`** - Usar Provider registry en lugar de búsqueda directa
6. **Actualizar `app/api/v1/endpoints/agente.py`** - Inyectar provider según estado
7. **Agregar endpoint `/api/v1/catalogo/estado`** - Frontend consulta estado

### FASE 2: INTELIGENCIA CONVERSACIONAL AVANZADA (PARALELO - ALTA PRIORIDAD)
**Objetivo**: IA entiende, razona y ayuda SIN catálogo real

1. **Mejorar NLU** (`app/services/nlu/`) - Intents, entities, Colombian Spanish
2. **Memory/Context Manager** (`app/services/conversation/`) - Sesión, preferencias, historial
3. **Recipe Engine** (`app/services/recipes/`) - Ya existe, mejorar mapeo conceptual
4. **Budget Planner** (`app/services/budget/`) - Listas de mercado por presupuesto
5. **Comparison Engine** (`app/services/comparison/`) - Comparativas conceptuales
6. **Cart Manager conversacional** - Agregar/modificar/quitar desde chat

### FASE 3: GOOGLE AUTH COMPLETO (CRÍTICO - SEGURIDAD)
**Objetivo**: OAuth 2.0 + Google Authenticator (TOTP) funcionando REALES

1. **Google OAuth** - Implementar `google-auth` library, verificar signature con JWKS
2. **Google Authenticator (TOTP)** - Ya implementado, verificar y probar E2E
3. **Account Linking** - Unificar Google OAuth + email/password + TOTP
4. **Tests E2E** - Playwright: login Google, setup 2FA, login con 2FA

### FASE 4: WOMPI PRODUCCIÓN (CRÍTICO - NEGOCIO)
**Objetivo**: Pasarela pagos funcional end-to-end en sandbox

1. **Configurar credenciales sandbox** - Documentar variables requeridas
2. **Tests E2E sandbox** - Flujo completo: carrito → checkout → Wompi → webhook → orden pagada
3. **Manejo errores** - Declined, pending, expired, network errors
4. **Idempotencia webhook** - Garantizar no duplicados

### FASE 5: TESTS DE INTEGRACIÓN COMPLETOS
**Objetivo**: Batería de pruebas que valide IA en ambos estados

1. **Conversation Fixtures** - 50+ casos: typos, voz, recetas, presupuesto, comparación
2. **MockProvider Fixtures** - Datos semilla tipados para tests
3. **E2E Playwright** - Flujos completos usuario real
4. **CI Pipeline** - GitHub Actions para tests automatizados

### FASE 6: DOCUMENTACIÓN MASCONTROL + PREPARACIÓN INTEGRACIÓN
**Objetivo**: Lista técnica precisa para conexión futura

1. **Investigar MasControl** - API, DB, esquemas, auth, webhooks
2. **Documento técnico** - `MASCONTROL_INTEGRATION_SPEC.md`
3. **Adapter skeleton** - Implementar cuando tengamos credenciales

---

## ARCHIVOS A CREAR/MODIFICAR (FASE 1 - INMEDIATO)

### Nuevos:
- `app/core/catalog_state.py` - Estado catálogo + feature flags
- `app/services/providers/__init__.py` - Registry
- `app/services/providers/base.py` - Protocol ProductProvider
- `app/services/providers/mock_provider.py` - Mock con fixtures colombianos
- `app/services/providers/mascontrol_provider.py` - Stub + doc
- `app/services/nlu/__init__.py` - Motor NLU
- `app/services/nlu/intent_classifier.py` - Clasificación intención
- `app/services/nlu/entity_extractor.py` - Extracción entidades
- `app/services/conversation/__init__.py` - Gestor conversación
- `app/services/conversation/memory.py` - Memoria contextual
- `app/schemas/provider.py` - Schemas de productos normalizados
- `tests/fixtures/mock_catalog.py` - Fixtures para tests
- `tests/conversation_test_cases.py` - 50+ casos de prueba
- `MASCONTROL_INTEGRATION_SPEC.md` - Especificación técnica

### Modificar:
- `app/services/agente.py` - Usar Provider registry
- `app/api/v1/endpoints/agente.py` - Inyección provider + endpoint estado
- `app/core/config.py` - Feature flag `CATALOG_CONNECTED`
- `frontend/src/lib/api.ts` - Tipos estado catálogo
- `frontend/src/components/ChatAgente.tsx` - Mostrar estado catálogo

---

## CRITERIOS DE ÉXITO FASE 1

- [ ] IA responde coherentemente SIN catálogo real (MockProvider)
- [ ] IA responde coherentemente CON catálogo real (cuando se conecte)
- [ ] Transición A→B por config, sin cambios de código
- [ ] Tests pasan con MockProvider
- [ ] Frontend muestra badge "Catálogo: Modo Demo / Conectado"
- [ ] No hay referencias hardcodeadas a seed_data en agente

---

## PRÓXIMOS PASOS INMEDIATOS (ESTA SESIÓN)

1. ✅ Inspección completa del repo (HECHO)
2. 🔄 Crear `MASTER_PLAN.md` (ESTE ARCHIVO)
3. 🔄 Implementar FASE 1: Provider Pattern + Estado Dual
4. 🔄 Implementar FASE 2 (parcial): NLU mejorado + Memory
5. 🔄 Implementar FASE 3: Google OAuth seguro + TOTP E2E
6. 🔄 Implementar FASE 4: Wompi sandbox E2E
7. 🔄 Tests de integración + Documentación MasControl

---

## NOTAS TÉCNICAS CLAVE

### MockProvider - Datos Fixture Realistas (NO inventados)
- Usar los 85 productos de `seed_data.py` como BASE de fixtures
- Etiquetar CLARAMENTE como `fuente: "fixture_desarollo"`
- Precios/Stock realistas pero marcados como demo
- Permitir testear: recetas, comparativas, presupuesto, stock 0, alternativas

### MasControl - Lo que NECESITAREMOS investigar
- ¿API REST? ¿GraphQL? ¿DB directa? ¿CSV/SFTP?
- Autenticación: OAuth2? API Key? JWT? mTLS?
- Esquema productos: SKU, EAN13, variantes, presentaciones
- Precios: Lista, por sede, por cliente, promociones, vigencia
- Stock: Tiempo real? Batch? Por bodega/sede?
- Webhooks: Cambios precio? Stock? Nuevos productos?
- Rate limits, paginación, versionado
- Entorno sandbox vs producción

### Seguridad - NO NEGOCIABLE
- Google OAuth: `google-auth` library + JWKS verification
- Wompi: Verificación server-to-server OBLIGATORIA
- TOTP: Rate limiting, códigos recuperación, backup codes
- Secrets: Solo en .env / vault, NUNCA en código

---

## COMANDOS DE VERIFICACIÓN RÁPIDA

```bash
# Levantar stack completo
cd /home/brayana/Economia-Aya/la_economia_app
docker compose up -d --build

# Ver logs
docker compose logs -f api

# Poblar BD + embeddings (cuando Ollama listo)
docker compose exec api python -m app.seed_data
docker compose exec api python -m app.scripts_ingesta_catalogo

# Tests
docker compose exec api pytest tests/ -v

# Frontend
cd frontend && npm run dev
```

---

**ESTADO**: Listo para iniciar FASE 1 - Provider Pattern + Estado Dual
**PRIORIDAD**: CRÍTICA - Desbloquea desarrollo IA sin catálogo real
