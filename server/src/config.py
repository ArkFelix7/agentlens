"""Server configuration via pydantic-settings. All settings can be overridden via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./agentlens.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8766
    debug: bool = False

    # CORS — allow dashboard dev server and production
    cors_origins: list[str] = ["*"]

    # Hallucination detection
    similarity_threshold_critical: float = 0.75
    similarity_threshold_warning: float = 0.85

    # Session limits
    max_sessions: int = 1000
    max_events_per_session: int = 50000

    class Config:
        env_prefix = "AGENTLENS_"
        env_file = ".env"


settings = Settings()
