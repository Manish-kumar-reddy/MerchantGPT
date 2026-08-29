from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://merchantgpt:merchantgpt@localhost:5432/merchantgpt"
    database_url_sync: str = "postgresql+psycopg2://merchantgpt:merchantgpt@localhost:5432/merchantgpt"

    # Auth
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7  # 7 days

    # CORS
    cors_allowed_origins: str = "http://localhost:3000"

    # Claude (used by app/services/campaign.py for campaign copy polish + weekly report narrative)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    anthropic_max_tokens: int = 2048

    # Gemini (used by app/agent/gemini_client.py for the chat agent's tool-calling loop)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_max_output_tokens: int = 2048

    # Embeddings (local, offline -- see app/services/embedding.py)
    embedding_dimension: int = 512

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
