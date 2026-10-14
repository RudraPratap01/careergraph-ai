"""
CareerGraph AI — Backend Configuration
Reads all settings from environment variables.
Secrets must NEVER be hardcoded here.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ─── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "CareerGraph AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"   # development | staging | production

    # ─── Database ───────────────────────────────────────────────────────────
    # For local dev without Docker, use SQLite.
    # Switch to postgresql+psycopg2://... once Docker / Postgres is available.
    DATABASE_URL: str = "sqlite:///./careergraph_dev.db"

    # ─── JWT ────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-before-any-deployment"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24   # 24 hours

    # ─── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ─── Neo4j (Phase 6) ────────────────────────────────────────────────────
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "change-this-too"

    # ─── LLM / OpenRouter (Phase 7+) ────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "openai/gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    lru_cache means this is computed only once per process — fast and safe.
    """
    return Settings()
