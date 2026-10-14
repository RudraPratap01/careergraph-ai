from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router

__all__ = ["auth_router", "health_router", "profile_router", "resume_router"]
