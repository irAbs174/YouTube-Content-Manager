"""Application factory + lifespan orchestration.

Startup: create tables → seed sample data (once, if empty) → start the
render worker. Shutdown: stop the worker cleanly.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from app.api.routes import auth, content, dashboard, health, meta, renders, scenes, series
from app.core.config import Settings
from app.core.constants import APP_NAME
from app.core.errors import DomainError
from app.db.base import Base
from app.db.seed import seed
from app.db.session import build_engine, build_session_factory
from app.rendering.queue import RenderQueue
from app.rendering.renderer import FfmpegRenderer, Renderer

logger = logging.getLogger("app")


def create_app(
    settings: Settings | None = None,
    renderer: Renderer | None = None,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(settings)
        app.state.engine = engine
        app.state.session_factory: sessionmaker = build_session_factory(engine)

        if settings.create_tables_on_startup:
            Base.metadata.create_all(engine)

        if settings.seed_on_startup:
            with app.state.session_factory() as session:
                created = seed(session)
                if created:
                    logger.info("seeded %s sample episodes", created)

        app.state.render_queue = RenderQueue(
            settings, app.state.session_factory, renderer or FfmpegRenderer(settings)
        )
        await app.state.render_queue.start()

        yield
        await app.state.render_queue.stop()
        engine.dispose()

    app = FastAPI(
        title=APP_NAME,
        version="0.2.0",
        lifespan=lifespan,
        # The JSON contract is camelCase; route handlers produce it explicitly.
        default_response_class=JSONResponse,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError):
        return JSONResponse({"error": exc.message}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        """The frontend expects `{error}` with 400 — not FastAPI's 422 `detail`."""
        first = exc.errors()[0] if exc.errors() else None
        message = "Invalid request body"
        if first:
            loc = ".".join(str(part) for part in first.get("loc", []) if part != "body")
            message = f"Invalid value for `{loc}`: {first.get('msg', 'invalid')}"
        return JSONResponse({"error": message}, status_code=400)

    for route_module in (health, meta, auth, dashboard, content, renders, series, scenes):
        app.include_router(route_module.router)

    return app


app = create_app()
