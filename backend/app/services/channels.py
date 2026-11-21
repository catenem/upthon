"""Canais e tópicos do Telegram: criação, tópicos de fórum e acesso dos workers."""
from __future__ import annotations

import asyncio
import logging

from telethon import functions, types
from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest, ToggleForumRequest
from telethon.tl.types import ChatAdminRights

from app.core.errors import ServiceUnavailable
from app.utils.text import topic_title
from app.services.workers import TelegramWorker, WorkerPool

_WORKER_RIGHTS = dict(post_messages=True, edit_messages=True, delete_messages=True, invite_users=True)


def normalize_channel_id(raw: object) -> int | None:
    """'123' -> -100123; '-100123' e outros negativos ficam como estão; inválido -> None."""
    text = str(raw).strip()
    if not text.replace("-", "").isdigit():
        return None
    value = int(text)
    return value if value < 0 else int(f"-100{value}")


class ChannelService:
    def __init__(self, pool: WorkerPool) -> None:
        self.pool = pool

    async def create_channel(self, name: str, *, is_topic: bool = False) -> int:
        """O admin cria o canal (ou supergrupo-fórum) e promove os bots a administradores."""
        admin = self.pool.admin
        if not admin:
            raise ServiceUnavailable("Não foi encontrada nenhuma conta de administrador para criar o canal.")

        result = await admin.client(
            CreateChannelRequest(
                title=name,
                about="Curso organizado",
                megagroup=is_topic,
                broadcast=not is_topic,
            )
        )
        channel = result.chats[0]
        if is_topic:
            await admin.client(ToggleForumRequest(channel=channel, enabled=True))

        for bot in (w for w in self.pool.workers if w.is_bot):
            try:
                await admin.client(
                    EditAdminRequest(
                        channel=channel,
                        user_id=bot.identifier,
                        admin_rights=ChatAdminRights(**_WORKER_RIGHTS),
                        rank="Upthon Worker",
                    )
                )
            except Exception as exc:
                logging.error("Falha ao configurar bot %s: %s", bot.identifier, exc)
        return channel.id

    async def get_or_create_topic(self, chat_id: int, topic_name: str) -> int | None:
        """Id do tópico com esse nome; cria se não existir. None em caso de falha.

        O título é sempre a versão limpa (sem '_'). Tópicos criados antes com o nome bruto
        ('02_-_MODULO_01') também são reconhecidos, para não duplicar.
        """
        raw_name = topic_name
        topic_name = topic_title(topic_name)
        admin = self.pool.admin
        if not admin:
            logging.error("Sem conta admin para criar o tópico '%s'.", topic_name)
            return None
        try:
            try:
                topics = await admin.client(
                    functions.channels.GetForumTopicsRequest(
                        channel=chat_id, offset_date=0, offset_id=0, offset_topic=0, limit=100, q=""
                    )
                )
                for topic in topics.topics:
                    if topic.title in (topic_name, raw_name):
                        return topic.id
            except Exception as exc:
                logging.warning("Não consegui listar tópicos (%s); vou criar '%s'.", exc, topic_name)

            result = await admin.client(
                functions.channels.CreateForumTopicRequest(channel=chat_id, title=topic_name)
            )
            for update in result.updates:
                if hasattr(update, "message") and hasattr(update.message, "id"):
                    return update.message.id
            if hasattr(result.updates[0], "id"):
                return result.updates[0].id
            return None
        except Exception:
            logging.exception("Erro crítico ao obter/criar tópico '%s'", topic_name)
            return None

    async def ensure_access(self, workers: list[TelegramWorker], channel_id: int) -> bool:
        """Garante que cada worker enxerga o canal. False = abortar o upload."""
        for worker in workers:
            if not await self._ensure_one(worker, channel_id):
                return False
        return True

    async def _ensure_one(self, worker: TelegramWorker, channel_id: int) -> bool:
        try:
            await worker.client.get_entity(channel_id)
            return True
        except ValueError:
            pass

        try:
            await worker.client.get_dialogs(limit=None)
            await worker.client.get_entity(channel_id)
            return True
        except Exception as exc:
            logging.error("Falha na sincronização profunda para %s: %s", worker.identifier, exc)

        admin = self.pool.admin
        if admin and worker.is_bot:
            try:
                channel = await admin.client.get_entity(channel_id)
                bot_me = await worker.client.get_me()
                await admin.client(
                    EditAdminRequest(
                        channel=channel,
                        user_id=bot_me,
                        admin_rights=ChatAdminRights(**_WORKER_RIGHTS),
                        rank="Worker",
                    )
                )
                await asyncio.sleep(1.5)
                await worker.client.get_dialogs(limit=5)
                await worker.client.get_entity(channel_id)
            except Exception as exc:
                logging.error("Falha crítica ao injetar %s: %s", worker.identifier, exc)
            return True  # um bot sem acesso não impede os demais workers

        logging.error("ERRO FATAL: o utilizador %s não encontrou o canal %s.", worker.identifier, channel_id)
        return False