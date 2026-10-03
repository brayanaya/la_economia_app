# La Economía Aya — Backend API

Backend del monolito modular (FastAPI + PostgreSQL/pgvector) para el
Supermercado La Economía Aya (sedes Santa Isabel y Machines, Neiva,
Huila). Expone el catálogo unificado, la comparativa de inventario
multisede, el endpoint de sincronización con Siigo y el retriever
semántico del pipeline RAG del agente de IA.

## Stack técnico

| Capa | Tecnología |
|---|---|
| API | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async, driver `asyncpg`) |
| Migraciones | Alembic |
| Base de datos | PostgreSQL 16 + `pgvector` |
| Embeddings | Sentence-Transformers (local, por defecto) u OpenAI `text-embedding-3-small` |
| Validación | Pydantic v2 |

---

## 1. Requisitos previos (Windows)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y con WSL2 habilitado.
- Python 3.11+ instalado y disponible en el PATH (`python --version`).
- VS Code con la terminal configurada en PowerShell.

---

## 2. Levantar Docker Desktop y la base de datos (PowerShell)

Docker Desktop debe estar corriendo antes de `docker compose up`. El
siguiente bloque verifica su estado, lo inicia si está apagado, espera a
que el daemon responda, y luego levanta los servicios.

```powershell
# 1. Verificar si el motor de Docker responde; si no, iniciar Docker Desktop
$dockerListo = $false
try {
    docker info | Out-Null
    $dockerListo = $true
} catch {
    $dockerListo = $false
}

if (-not $dockerListo) {
    Write-Host "Docker Desktop no está corriendo. Iniciando..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    # Esperar hasta que el daemon responda (máximo ~90 segundos)
    $intentos = 0
    do {
        Start-Sleep -Seconds 5
        $intentos++
        try {
            docker info | Out-Null
            $dockerListo = $true
        } catch {
            $dockerListo = $false
        }
    } while (-not $dockerListo -and $intentos -lt 18)

    if (-not $dockerListo) {
        Write-Error "Docker Desktop no respondió a tiempo. Ábrelo manualmente y reintenta."
        exit 1
    }
}

Write-Host "Docker Desktop está activo." -ForegroundColor Green

# 2. Preparar variables de entorno (solo la primera vez)
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creó .env a partir de .env.example. Revísalo antes de continuar." -ForegroundColor Yellow
}

# 3. Levantar PostgreSQL (+ API, si se desea usar el contenedor en vez del entorno local)
docker compose up -d postgres

# 4. Verificar el estado del contenedor
docker compose ps
docker compose logs -f postgres
```

---

## 3. Crear el entorno virtual de Python (PowerShell)

```powershell
# Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Si PowerShell bloquea la activación por política de ejecución, ejecutar
# una sola vez (como administrador) y reintentar:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Ejecutar las migraciones de Alembic

Con `postgres` corriendo en Docker (paso 2) y el entorno virtual activo:

```powershell
alembic upgrade head
```

> Nota: si la base de datos ya fue inicializada por Docker mediante
> `db/init.sql` (primera vez que se crea el volumen), las tablas ya
> existen. En ese caso, marca la migración baseline como aplicada sin
> volver a ejecutar el DDL:
> ```powershell
> alembic stamp 0001
> ```
> Para un entorno nuevo (por ejemplo, en otra máquina, sin pasar por
> `init.sql`), usa `alembic upgrade head` directamente para crear el
> esquema desde cero.

---

## 5. Ejecutar la API en modo desarrollo

```powershell
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 6. Poblar los embeddings del catálogo (pipeline RAG)

Una vez que `productos` y `categorias` tienen datos (por ejemplo, los del
`db/seed.sql`), genera los vectores semánticos:

```powershell
python -m app.scripts_ingesta_catalogo
```

Por defecto usa `EMBEDDING_PROVIDER=sentence_transformers` (modelo local,
sin costo). Para usar OpenAI en su lugar, edita `.env`:

```
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## 7. Probar el retriever semántico

```powershell
$body = @{
    consulta = "quiero algo bajo en grasa para el desayuno"
    sede_id  = "a0000000-0000-0000-0000-000000000001"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
    -Uri "http://localhost:8000/api/v1/busqueda/semantica" `
    -ContentType "application/json" `
    -Body $body
```

---

## 8. Estructura del proyecto

```text
la_economia_app/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── productos.py     # RF-01, RF-09
│   │   │   ├── inventario.py    # RF-06, RF-05/RF-08 (sync Siigo)
│   │   │   └── busqueda.py      # Retriever RAG (numeral 10.3)
│   │   └── router.py
│   ├── core/
│   │   ├── config.py            # Settings (Pydantic v2)
│   │   └── database.py          # Motor async + Base declarativa
│   ├── models/                  # SQLAlchemy 2.0 (ORM)
│   ├── schemas/                 # Pydantic v2 (contratos de la API)
│   ├── services/
│   │   └── embeddings.py        # Proveedor de embeddings (OpenAI / ST)
│   ├── scripts_ingesta_catalogo.py
│   └── main.py
├── alembic/                     # Migraciones de base de datos
├── db/
│   ├── init.sql                 # Esquema (usado por Docker en 1ra init)
│   └── seed.sql                 # Datos de prueba
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 9. Próximos pasos sugeridos

- Middleware de consumo de la cola `transacciones_siigo` (worker en
  segundo plano, desacoplado del proceso web de FastAPI).
- Autenticación (OAuth2/JWT) sobre los endpoints administrativos y de
  middleware, conforme a RNF-04.
- Servicio del agente de IA (orquestación del prompt + LLM), que
  consume `POST /api/v1/busqueda/semantica` como su retriever.
