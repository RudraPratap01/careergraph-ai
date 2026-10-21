"""
CareerGraph AI — FastAPI Application Entry Point

This file:
  1. Creates the FastAPI app instance
  2. Configures CORS (allows the React frontend to call the API)
  3. Registers all routers
  4. Creates database tables on startup (dev mode)
  5. Exposes API docs at /docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import create_tables
from app.routes.auth import router as auth_router
from app.routes.assessments import router as assessments_router
from app.routes.career import router as career_router
from app.routes.graph import router as graph_router
from app.routes.health import router as health_router
from app.routes.mentorship import router as mentorship_router
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router
from app.routes.roadmap import router as roadmap_router
from app.routes.verification import router as verification_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "CareerGraph AI — A career intelligence platform that analyzes student skills, "
        "identifies gaps, generates personalized roadmaps, and connects students with mentors."
    ),
    docs_url="/docs",          # Swagger UI — visit http://localhost:8000/docs
    redoc_url="/redoc",        # ReDoc alternative
)

# ─── CORS ────────────────────────────────────────────────────────────────────
# Without this, the browser blocks API calls from the React frontend (port 5173)
# to the FastAPI backend (port 8000) because they are on different ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(career_router)     # Phase 4 — skill gaps & readiness
app.include_router(graph_router)      # Phase 5 — skill dependency graph
app.include_router(roadmap_router)    # Phase 5 — learning roadmap
app.include_router(assessments_router)  # Phase 8 — skill assessments
app.include_router(mentorship_router)   # Phase 8 — alumni matching & mentorship
app.include_router(verification_router)  # Phase 6 — GitHub verification & LinkedIn link

# Additional routers will be registered here in later phases:
# app.include_router(rag_router)       # Phase 7


# ─── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """
    Runs once when the server starts.
    Creates DB tables in development.
    In production, Alembic migrations handle schema changes.
    """
    create_tables()
    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} started ({settings.ENVIRONMENT})")


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
