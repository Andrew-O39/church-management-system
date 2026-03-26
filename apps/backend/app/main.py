from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.health import healthz, readyz
from app.core.logging import configure_logging
from app.core.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Church Management System",
        version="0.1.0",
    )

    # ---- Logging ----
    configure_logging()

    # ---- CORS ----
    origins = [
        origin.strip()
        for origin in (settings.CORS_ORIGINS or "").split(",")
        if origin.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

