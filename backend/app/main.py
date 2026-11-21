"""Criação do app FastAPI: lifespan, CORS, handlers de erro e routers. Sem regra de negócio."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, bots, dashboard, files, uploads
from app.container import Container
from app.core.config import Settings, get_settings
from app.core.errors import UpthonError
from app.core.logging import setup_logging
from app.web import mount_frontend


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.info("Iniciando Upthon Backend...")
        container = Container(settings)
        await container.startup()
        app.state.container = container
        yield
        await container.shutdown()

    app = FastAPI(title="Upthon", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(UpthonError)
    async def upthon_error_handler(_: Request, exc: UpthonError):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception):
        # Mantém o comportamento antigo (500 + detail=str(e)), agora num único lugar.
        logging.exception("Erro não tratado")
        return JSONResponse({"detail": str(exc)}, status_code=500)

    for module in (auth, files, uploads, bots, dashboard):
        app.include_router(module.router)
    mount_frontend(app, settings.frontend_dir)   # por último: as rotas /api têm prioridade
    return app


app = create_app()
