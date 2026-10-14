"""
Database session factory.

SQLAlchemy is used for all DB access.
The DATABASE_URL in config determines the actual database:
  - SQLite  → local development (no Docker needed)
  - PostgreSQL → staging / production

Switching databases is a single env-variable change.
No code changes required.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# SQLite requires the connect_args flag; PostgreSQL does not.
# We handle this transparently here so the rest of the codebase
# doesn't need to know which DB is active.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,   # logs SQL when DEBUG=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this class.
    Keeps all models under one metadata registry,
    which is required for alembic migrations.
    """
    pass


def get_db():
    """
    FastAPI dependency that yields a database session per request.
    The session is always closed after the request, even on error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all tables defined in the models.
    Called on application startup for development.
    In production, use Alembic migrations instead.
    """
    # Import all models so Base.metadata knows about them
    from app.models import user, profile, resume  # noqa: F401
    Base.metadata.create_all(bind=engine)
