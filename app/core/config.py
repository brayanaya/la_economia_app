from urllib.parse import quote_plus
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Economia Aya API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

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

    anthropic_api_key: str = ""
    llm_model: str = "qwen2.5:7b"
    umbral_similitud_minima: float = 0.5
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_embedding_model: str = "nomic-embed-text"

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


settings = Settings()
