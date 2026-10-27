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
    # Switch to postgresql+psycopg2://... once PostgreSQL is available.
    DATABASE_URL: str = "sqlite:///./careergraph_dev.db"

    # ─── JWT ────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-before-any-deployment"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24   # 24 hours

    # ─── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ─── Neo4j (Phase 5 skill graph) ────────────────────────────────────────
    # GRAPH_BACKEND: "memory" (default, always available) or "neo4j".
    # With "neo4j", the app uses Neo4j only if the server is reachable and the
    # neo4j driver is installed; otherwise it falls back to the in-memory graph.
    GRAPH_BACKEND: str = "memory"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "change-this-too"

    # ─── Phase 7: grounded career intelligence ───────────────────────────────
    # Retrieval is always local and lexical. The configured LLM is optional:
    # without a key the API returns a deterministic, source-attributed answer.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: float = 20.0
    LLM_MAX_TOKENS: int = 600
    LLM_TEMPERATURE: float = 0.2
    RAG_TOP_K: int = 6
    RAG_MIN_SCORE: float = 1.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    lru_cache means this is computed only once per process — fast and safe.
    """
    return Settings()
