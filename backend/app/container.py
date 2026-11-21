"""Composição das dependências (substitui ``app.state.controller`` + flags soltas)."""
from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings
from app.db.repository import Repository
from app.services.bot_service import BotService
from app.services.channels import ChannelService
from app.services.dashboard import DashboardService
from app.services.queue_store import QueueStore
from app.services.telegram_session import TelegramSession
from app.services.upload_service import UploadService
from app.services.workers import WorkerPool


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo = Repository(settings.db_path)
        self.session = TelegramSession(self.repo)
        self.pool = WorkerPool(self.session, self.repo, settings)
        self.channels = ChannelService(self.pool)
        self.queue = QueueStore(settings.assets_dir)
        self.uploads = UploadService(self.pool, self.channels, self.queue, settings)
        self.bots = BotService(self.repo)
        self.dashboard = DashboardService(self.queue)
        self._background: set[asyncio.Task] = set()

    @property
    def is_authorized(self) -> bool:
        return self.session.authorized

    async def startup(self) -> None:
        self.settings.assets_dir.mkdir(parents=True, exist_ok=True)
        self.repo.init_schema()  # falha aqui deve derrubar o app, não iniciar "pela metade"

        if await self.session.restore():
            logging.info("Sucesso no Auto-Login. Ativando os uploaders...")
            await self.pool.setup()
        else:
            logging.warning("Auto-Login falhou. App iniciará desautenticado.")

        # Em segundo plano para não atrasar o startup (faz chamadas de rede).
        task = asyncio.create_task(self.bots.refresh_legacy_avatars())
        self._background.add(task)
        task.add_done_callback(self._background.discard)

    async def shutdown(self) -> None:
        logging.info("Desligando Upthon Backend...")
        for task in list(self._background):
            task.cancel()
        await self.pool.shutdown_bots()
        await self.session.disconnect()
