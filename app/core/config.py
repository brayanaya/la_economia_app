from urllib.parse import quote_plus
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Economia Aya API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    auth_cookie_name: str = "la_economia_session"
    auth_cookie_secure: bool = True
    auth_session_ttl_seconds: int = 1209600
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.56.1:3000", "http://localhost:8081"]

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    embedding_provider: str = "sentence_transformers"
    embedding_dimensions: int = 768
    sentence_transformers_model: str = "paraphrase-multilingual-mpnet-base-v2"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # ---- IA: generacion de respuestas del agente conversacional ----
    # llm_provider: "ollama" (local/gratuito), "anthropic" (API de Claude)
    # o "auto" (Claude si hay API key, si no Ollama; y si ninguno responde,
    # el agente usa un respondedor determinista con los productos recuperados).
    llm_provider: str = "auto"
    llm_model: str = "qwen2.5:7b"
    llm_max_tokens: int = 16000
    anthropic_api_key: str = ""
    anthropic_chat_model: str = "claude-opus-5-5"
    umbral_similitud_minima: float = 0.60
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_embedding_model: str = "nomic-embed-text"

    # ---- Pagos en linea (Wompi, Colombia) ----
    # Sin public key configurada los endpoints de pasarela responden 503 y el
    # checkout solo ofrece "contra entrega" / "Bre-B" (flujo actual).
    wompi_public_key: str = ""
    wompi_integrity_secret: str = ""
    wompi_events_secret: str = ""
    wompi_ambiente: str = "sandbox"  # "sandbox" | "produccion"
    wompi_checkout_url: str = "https://checkout.wompi.co/p/"
    wompi_api_base: str = ""  # se deriva del ambiente si queda vacio

    # URL publica del frontend; se usa para armar el redirect-url de Wompi.
    app_public_url: str = "http://localhost:3000"

    @property
    def wompi_api_base_resuelta(self) -> str:
        """Base de la API de transacciones de Wompi segun el ambiente."""
        if self.wompi_api_base:
            return self.wompi_api_base.rstrip("/")
        if self.wompi_ambiente == "produccion":
            return "https://production.wompi.co/v1"
        return "https://sandbox.wompi.co/v1"

    @property
    def wompi_configurada(self) -> bool:
        """La pasarela esta lista para iniciar pagos (public key + integridad)."""
        return bool(self.wompi_public_key and self.wompi_integrity_secret)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def armar_database_url(self):
        if not self.database_url:
            usuario = quote_plus(self.postgres_user)
            clave = quote_plus(self.postgres_password)
            self.database_url = (
                f"postgresql+asyncpg://{usuario}:{clave}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self

    @property
    def database_url_sync(self) -> str:
        """URL sincrona (psycopg2) para Alembic; la aplicacion usa asyncpg."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


settings = Settings()

