from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import api_router
from app.core.env_validation import log_production_warnings, validate_settings_for_environment
from app.core.health import healthz, readyz
from app.core.logging import configure_logging
from app.core.settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_settings_for_environment(settings)
    log_production_warnings(settings)
    yield


def _cors_origins() -> list[str]:
    raw = [o.strip() for o in (settings.CORS_ORIGINS or "").split(",") if o.strip()]
    if raw:
        return raw
    if settings.is_local_environment:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    # Non-local must set CORS_ORIGINS explicitly (validated again in production)
    return []


def create_app() -> FastAPI:
    app = FastAPI(
        title="Church Management System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ---- Logging ----
    configure_logging()

    origins = _cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    trusted = [h.strip() for h in (settings.TRUSTED_HOSTS or "").split(",") if h.strip()]
    if trusted:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)

    # ---- API Routes ----
    app.include_router(api_router)

    # ---- Health / readiness ----
    # Used by the frontend landing page to confirm wiring.
    app.add_api_route("/healthz", healthz, methods=["GET"], tags=["health"])
    app.add_api_route("/readyz", readyz, methods=["GET"], tags=["health"])

    # ---- Root ----
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"message": "Church Management System API. Use /healthz to check status."}

    return app


app = create_app()
