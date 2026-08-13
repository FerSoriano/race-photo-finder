"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from rpf.api.routes import admin, events, health, photos
from rpf.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title="Race Photo Finder",
        description="Find race photos by runner bib number.",
        version="0.1.0",
    )

    # Dev is permissive; production must pin real origins before launch.
    # PATCH and DELETE are listed because the admin panel calls them from a
    # browser, which sends a preflight the CLI never did.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment != "prod" else [],
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(photos.router)
    app.include_router(admin.router)

    # With STORAGE_BACKEND=local there is no CDN, so serve the files ourselves.
    # In production R2 serves them and this mount is never reached.
    if settings.storage_backend == "local":
        settings.local_storage_root.mkdir(parents=True, exist_ok=True)
        app.mount(
            "/media",
            StaticFiles(directory=settings.local_storage_root),
            name="media",
        )

    return app


app = create_app()
