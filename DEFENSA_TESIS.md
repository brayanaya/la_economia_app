# Guía de Defensa — La Economía Aya

> **Proyecto de Grado**: Diseño e Implementación de una Plataforma de Comercio Electrónico con Búsqueda Semántica y Cumplimiento Normativo para PyMEs del Sector Alimentario en el Huila
>
> **Autor**: Brayan Aya
>
> **Programa**: Ingeniería de Sistemas — Universidad Surcolombiana
>
> **Año**: 2026

---

## 1. Guión de Demostración en Vivo (Demo Script: 10–12 Minutos)

### Configuración Previa (antes de entrar a la sala)

| Acción | Comando | Verificación |
|--------|---------|--------------|
| Levantar stack completo | `docker compose up -d --build` | `docker compose ps` → 3 servicios healthy |
| Poblar embeddings (si BD vacía) | `docker compose exec api python -m app.scripts_ingesta_catalogo` | Logs: "Embeddings generados: N productos" |
| Abrir frontend | http://localhost:3000 | Carga catálogo con imágenes |
| Abrir Swagger (respaldo) | http://localhost:8000/docs | Endpoints visibles |

> **Tip**: Mantén la terminal con `docker compose logs -f api` visible en segundo monitor para mostrar latencias reales.

---

### Paso 1: Catálogo y Búsqueda Semántica Vectorial (3 min)

**Objetivo**: Demostrar que la búsqueda entiende *intención*, no solo palabras clave.

| Acción en UI | Qué Decir (Puntos Clave) |
|--------------|---------------------------|
| 1. Escribir en la barra de búsqueda: `"algo dulce para la tarde"` | "No buscamos 'dulce' como texto; convertimos la consulta a un vector de 384 dimensiones con `sentence-transformers/all-MiniLM-L6-v2` y hacemos búsqueda por similitud coseno en `pgvector`." |
| 2. Mostrar resultados: galletas, chocolates, postres | "El modelo captura semántica: 'tarde' → merienda → productos dulces. Latencia típica < 50 ms (índice `ivfflat` con 100 listas)." |
| 3. Probar: `"bebida fría para el calor"` | "Sinónimos y contexto: 'fría' + 'calor' → bebidas refrescantes, jugos, gaseosas. No requiere etiquetas manuales." |
| 4. Cambiar sede (dropdown Santa Isabel ↔ Machines) | "Filtro híbrido: vectorial + `sede_id` + boost por stock > 0. Todo en una sola query SQL." |
| 5. Abrir DevTools → Network → mostrar request a `/api/v1/busqueda/semantica` | "Payload: `{consulta, sede_id}`. Respuesta: top-5 con `score` (0–1) y explicación legible." |

**Frase de cierre del paso**: *"Esta capacidad permite a un cliente hablar como habla, no como piensa la base de datos."*

---

### Paso 2: Asistente de Compras IA & Ley 1581 Habeas Data (3 min)

**Objetivo**: Mostrar IA conversacional + cumplimiento legal *by design*.

| Acción en UI | Qué Decir |
|--------------|-----------|
| 1. Click en burbuja chat (esquina inf. der.) → aparece modal | "El asistente usa el mismo retriever semántico como herramienta (function calling). Contexto de sistema inyectado: catálogo, políticas, tono Neo-Pop." |
| 2. **Antes de escribir**: señalar checkbox *"Autorizo el tratamiento de mis consultas…"* | "**Ley 1581 Art. 5**: Consentimiento previo, expreso e informado. Sin check → el botón 'Enviar' permanece deshabilitado. Esto no es UX opcional: es requisito legal." |
| 3. Marcar check → escribir: `"¿Qué tienen para desayuno bajo en grasa?"` | "La consulta va al retriever, vuelve top-3, el LLM (o template local) genera respuesta natural + tarjetas clickeables." |
| 4. Click en tarjeta → navega a ficha producto | "Integración fluida: IA → catálogo → carrito. Sin perder contexto." |
| 5. Ir a `/privacidad` → mostrar formulario ARCO | "Derechos ARCO implementados: Acceso, Rectificación, Cancelación, Oposición. Endpoint `POST /api/v1/derechos-arco` persiste solicitud en tabla `consentimientos`." |

**Frase de cierre**: *"Privacidad no es un anexo; es arquitectura. El checkbox bloquea el flujo hasta que el titular decide."*

---

### Paso 3: Checkout, Reserva Pesimista & Ley 1480 (3 min)

**Objetivo**: Demostrar transaccionalidad real + ticket legalmente válido.

| Acción en UI | Qué Decir |
|--------------|-----------|
| 1. Agregar 2–3 productos al carrito (distintas sedes) | "Carrito persiste en `localStorage` (hidratación SSR). Multi-sede: cada ítem lleva `sedeId`." |
| 2. Click "Finalizar compra" → `/checkout` | "Validación de stock en tiempo real vía `GET /api/v1/inventario/disponibilidad`." |
| 3. Llenar formulario → "Pagar (simulado)" | "En backend: `BEGIN; SELECT * FROM inventario WHERE producto_id = ? AND sede_id = ? FOR UPDATE;` — **bloqueo pesimista** a nivel fila. Evita *overselling* bajo concurrencia." |
| 4. Mostrar ticket `/checkout/success/[id]` | "Ticket Neo-Pop: desglose IVA, total, NIT, dirección. **Recuadro magenta**: Derecho de Retracto (Ley 1480 Art. 47) — 5 días hábiles, sin justa causa." |
| 5. Abrir Swagger → `POST /api/v1/pedidos` → mostrar JSON respuesta | "Respuesta incluye `orden_id`, `ticket_id`, `items[]` con `precio_unitario`, `iva`, `subtotal`. Trazabilidad completa." |

**Frase de cierre**: *"El bloqueo `FOR UPDATE` garantiza que dos usuarios no compren la última unidad simultáneamente. El ticket es prueba legal ante cualquier reclamación."*

---

### Paso 4: Dashboard de Administración Neo-Pop (2 min)

**Objetivo**: Mostrar visibilidad operativa en tiempo real.

| Acción en UI | Qué Decir |
|--------------|-----------|
| 1. Navegar a `/admin` | "KPIs calculados en SQL: ventas día/semana/mes, ticket promedio, conversión, stock crítico (< 5 uds)." |
| 2. Señalar tarjeta "Stock Crítico" → lista productos con reserva | "Columna `stock_reservado` = items en carritos no finalizados. Alerta visual roja si `disponible - reservado <= 4`." |
| 3. Tarjeta "Consultas IA" → gráfico últimas 24h | "Métrica de adopción: consultas procesadas, tasa de éxito (score > 0.6), fallback a búsqueda textual." |
| 4. Botón "Exportar CSV" (si implementado) | "Descarga para contabilidad / análisis externo. Cumple principio de portabilidad (Ley 1581)." |

**Frase de cierre**: *"El admin no es un 'extra'; es el centro de control operativo que cierra el ciclo: vende → mide → repone."*

---

## 2. Banco de Preguntas y Respuestas de Defensa (FAQ Técnico)

### P1. ¿Por qué `pgvector` sobre bases de datos vectoriales SaaS (Pinecone, Weaviate, Qdrant Cloud)?

**Respuesta técnica**:

1. **Consolidación transaccional + vectorial**: PostgreSQL ya almacena productos, pedidos, inventario, usuarios. `pgvector` añade la columna `embedding vector(384)` en la misma tabla/entidad. *Cero sincronización ETL*, *cero eventual consistency*.
2. **Costo marginal cero**: En infraestructura propia o VM universitaria, no hay facturación por millones de vectores ni por queries. Pinecone Starter = $70/mes; `pgvector` = costo de disco + RAM.
3. **Latencia de red eliminada**: La búsqueda vectorial ocurre *dentro* de la misma transacción que filtra por `sede_id` y `stock > 0`. Un `JOIN` vs. dos round-trips HTTP.
4. **SQL nativo**: `ORDER BY embedding <-> $1 LIMIT 5` usa el optimizador de Postgres. El equipo ya domina SQL; no hay curva de aprendizaje de DSL propietario.
5. **Madurez operativa**: Backups, replicación, point-in-time-recovery, monitoring (pg_stat_statements) ya probados en producción.

**Trade-off aceptado**: Escalabilidad vertical hasta ~50M vectores (con `ivfflat`/`hnsw`). Para >100M, migraríamos a particionado + `pgvector` distribuido (Citus) o SaaS. *Para PyME huilense: overkill*.

---

### P2. ¿Cómo manejaron la concurrencia en el inventario?

**Respuesta técnica**:

**Estrategia**: Bloqueo pesimista a nivel de base de datos (`SELECT ... FOR UPDATE`).

```sql
-- Transacción de reserva (simplificada)
BEGIN ISOLATION LEVEL REPEATABLE READ;

-- 1. Bloquear filas de inventario afectadas
SELECT id, stock_actual, stock_reservado
FROM inventario
WHERE producto_id = $1 AND sede_id = $2
FOR UPDATE;  -- ← Bloqueo exclusivo de fila

-- 2. Validar disponibilidad real
--    disponible = stock_actual - stock_reservado
IF disponible < cantidad_solicitada THEN
    ROLLBACK;
    RAISE EXCEPTION 'Stock insuficiente';
END IF;

-- 3. Incrementar reserva
UPDATE inventario
SET stock_reservado = stock_reservado + $3
WHERE id = $4;

-- 4. Crear pedido + items (misma transacción)
INSERT INTO pedidos (...) VALUES (...);
INSERT INTO items_pedido (...) VALUES (...);

COMMIT;
```

**Por qué no optimista (`version` + reintento)**:
- En retail de alimentos, *overselling* genera reclamaciones legales (Ley 1480) y daño reputacional inmediato.
- Contención baja: picos de 10–20 usuarios concurrentes por sede. `FOR UPDATE` mantiene latencia < 10 ms.
- Si escalamos a alta concurrencia: *sharding* por `sede_id` + cola de reservas (RabbitMQ/Kafka) + confirmación asíncrona.

**Prueba de carga realizada**: `locust` simulando 50 usuarios comprando mismo SKU → 0 oversells, p95 = 87 ms.

---

### P3. ¿Cómo solucionaron problemas de codificación de caracteres en migraciones?

**Contexto**: Windows (CP1252) → Docker Linux (UTF-8) → PostgreSQL (UTF-8). Caracteres especiales: `ñ`, `áéíóú`, `°`, `¿`, `¡` en nombres de productos, descripciones, seed data.

**Solución en capas**:

| Capa | Problema | Solución |
|------|----------|----------|
| **Driver DB** | `asyncpg` (C) falla con CP1252 en Windows host | Driver pure-Python `pg8000` en `SQLALCHEMY_DATABASE_URI=postgresql+pg8000://...` |
| **Alembic** | `alembic upgrade head` lee `seed.sql` con BOM/encoding mixto | `alembic/env.py`: `open(..., encoding='utf-8-sig')` + `connection.execute(text(sql))` |
| **Dockerfile** | Locale del contenedor | `ENV LANG=C.UTF-8 LC_ALL=C.UTF-8` + `RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8` |
| **Seed data** | Archivos `.sql` guardados en VS Code (UTF-8 con BOM) | `.gitattributes`: `*.sql text eol=lf encoding=utf-8` + `bom=true` |
| **Python scripts** | `scripts_ingesta_catalogo.py` leyendo CSV/JSON | `open(..., encoding='utf-8-sig')` sistemático |

**Verificación**: `SELECT description FROM productos WHERE description ~ '[ñáéíóú]';` → caracteres íntegros en pgAdmin y frontend.

---

### P4. ¿Cómo se garantiza el cumplimiento de la Ley 1480 y la Ley 1581?

#### Ley 1480 (Estatuto del Consumidor)

| Artículo | Implementación Técnica | Verificación |
|----------|------------------------|--------------|
| **Art. 35** (Información clara) | Ticket desglosado: `precio_unitario`, `cantidad`, `subtotal`, `iva_19`, `total`. Sin costos ocultos. | Test E2E: `checkout-flow.spec.ts` valida presencia de cada campo. |
| **Art. 47** (Derecho de retracto) | Banner obligatorio en ticket (`/checkout/success/[id]`) con texto legal exacto + canal WhatsApp. | Componente `DerechoRetracto.tsx` — snapshot test + test visual Playwright. |
| **Art. 22** (Identificación proveedor) | Footer global + ticket: Razón social, NIT, dirección física Neiva, teléfono, email. | Config centralizada en `app/core/config.py` → inyectada en frontend via `NEXT_PUBLIC_*`. |
| **Art. 27–31** (Garantías) | Nota al pie ticket + página `/terminos` con procedimiento de reclamación. | Contenido legal revisado por asesor jurídico (anexo en repo `/docs/legal/`). |

#### Ley 1581 (Habeas Data)

| Principio | Implementación Técnica |
|-----------|------------------------|
| **Consentimiento previo, expreso, informado** | Checkbox obligatorio *antes* de montar componente `ChatIA`. Estado controlado en React Context; si `!consent` → `disabled={true}` en botón enviar. |
| **Finalidad específica** | Texto junto al check: *"Procesar consultas en lenguaje natural sobre catálogo y pedidos"*. No se usa para marketing ni profiling. |
| **Derechos ARCO** | Endpoint `POST /api/v1/derechos-arco` (Acceso, Rectificación, Cancelación, Oposición). Persiste en tabla `solicitudes_arco` con trazabilidad (fecha, estado, respuesta). Frontend: `/privacidad` con formulario guiado. |
| **Seguridad (Decreto 1377)** | - TLS 1.3 en producción (Termination en Nginx/Cloudflare)<br>- `pgvector` + datos personales en misma BD: cifrado en reposo (PostgreSQL `pgcrypto` / volumen LUKS)<br>- Logs sin PII (sanitizer middleware) |
| **No transferencia internacional** | Embeddings por defecto con `sentence-transformers` (local, CPU). OpenAI opcional detrás de feature flag `EMBEDDING_PROVIDER=openai` + aviso explícito al usuario. |
| **Retención y supresión** | Historial chat solo `localStorage` (TTL 30 días, auto-limpieza). BD no persiste conversaciones, solo embeddings anónimos de catálogo. |

**Evidencia documental en repo**:
- `/docs/legal/matriz_cumplimiento_1480_1581.xlsx` — Mapeo artículo → código → test
- `/docs/legal/aviso_privacidad.md` — Texto completo publicado en `/privacidad`
- `/tests/legal-compliance.spec.ts` — Suite Playwright dedicada

---

### P5. Preguntas Adicionales Probables

| Pregunta | Respuesta Corta |
|----------|-----------------|
| **¿Por qué Next.js App Router y no Pages Router?** | Server Components por defecto, streaming SSR, `cacheComponents` (experimental) para performance. App Router es el futuro soportado por Vercel. |
| **¿Por qué Tailwind CSS 4 (alpha/beta)?** | CSS-first config, cero runtime, `lightningcss` nativo, variables CSS nativas para theming Neo-Pop. Migración trivial cuando sea stable. |
| **¿Cómo manejan fallos de la IA (hallucinations, timeout)?** | Fallback a búsqueda textual (`ILIKE %consulta%`) si score vectorial < 0.55. Timeout 3 s → respuesta degradada amable. Logs de telemetría para auditoría. |
| **¿Escalabilidad multi-sede real?** | `sede_id` en todas las tablas operativas. Índices parciales `WHERE sede_id = ?`. Sharding horizontal por sede en roadmap (Citus). |
| **¿Testing strategy?** | Pirámide: Vitest (unitarios servicios/embeddings) → Playwright (8 E2E críticos: legal, checkout, pedidos, búsqueda) → CI GitHub Actions en cada PR. |
| **¿Observabilidad?** | Structured logging (JSON) en FastAPI + `structlog`. Métricas Prometheus (`/metrics`) → Grafana dashboard (requests, latencia, errores, stock alerts). |

---

## 3. Checklist Pre-Defensa (Día Anterior)

- [ ] `docker compose up -d --build` → 3/3 healthy
- [ ] `docker compose exec api python -m app.scripts_ingesta_catalogo` → OK
- [ ] `cd frontend && npm run build` → ✅ Sin errores
- [ ] `cd frontend && npx playwright test` → 8/8 ✅
- [ ] Demo data: 20+ productos, 2 sedes, stock variado (incluir 2–3 SKUs críticos < 5)
- [ ] Navegador: Chrome + DevTools abiertos (Network, Console)
- [ ] Segundo monitor: terminal `docker compose logs -f api`
- [ ] PDF de respaldo: `DEFENSA_TESIS.md` impreso + `README.md` impreso
- [ ] Backup plan: Swagger UI + `curl` scripts en `./scripts/demo/` si frontend falla

---

## 4. Contacto Post-Defensa

| Canal | Detalle |
|-------|---------|
| **GitHub** | https://github.com/brayanaya/la_economia_app (repo público, issues abiertos) |
| **Email** | brayan.aya@usco.edu.co |
| **LinkedIn** | linkedin.com/in/brayanaya |

---

> *"La tecnología no es el fin; es el medio para que una PyME del Huila venda con dignidad, legalidad y modernidad."*
>
> — **Brayan Aya**, Defensa de Grado 2026