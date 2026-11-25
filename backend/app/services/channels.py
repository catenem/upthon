"""Canais e tópicos do Telegram: criação, tópicos de fórum e acesso dos workers."""
from __future__ import annotations

import asyncio
import logging

from telethon import errors, functions, types
from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest, ToggleForumRequest
from telethon.tl.types import ChatAdminRights

from app.core.errors import ServiceUnavailable
from app.utils.text import topic_title
from app.services.workers import TelegramWorker, WorkerPool

BOT_VISIBILITY_DELAYS = (1.5, 3.0, 6.0)   # segundos entre conferências (alterado nos testes)
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

    async def ensure_access(self, workers: list[TelegramWorker], channel_id: int) -> list[TelegramWorker]:
        """Devolve os workers que enxergam o canal. Lista vazia = abortar o upload.

        Conta de usuário sem acesso é fatal (é ela que cria canais e tópicos). Bot sem acesso só
        fica de fora do rodízio desta execução: mandar por ele só geraria erros e itens pulados.
        """
        usable: list[TelegramWorker] = []
        for worker in workers:
            if await self._ensure_one(worker, channel_id):
                usable.append(worker)
            elif not worker.is_bot:
                return []
            else:
                logging.warning("Bot %s sem acesso ao canal %s: fora do rodízio nesta execução.", worker.identifier, channel_id)
        return usable

    @staticmethod
    async def _can_see(worker: TelegramWorker, channel_id: int) -> bool:
        try:
            await worker.client.get_entity(channel_id)
            return True
        except (ValueError, errors.RPCError):
            return False

    async def _ensure_one(self, worker: TelegramWorker, channel_id: int) -> bool:
        if await self._can_see(worker, channel_id):
            return True

        if not worker.is_bot:
            # Conta de usuário: carrega todos os diálogos para o canal entrar no cache.
            try:
                await worker.client.get_dialogs(limit=None)
            except Exception as exc:
                logging.error("Falha na sincronização profunda para %s: %s", worker.identifier, exc)
            if await self._can_see(worker, channel_id):
                return True
            logging.error("ERRO FATAL: o utilizador %s não encontrou o canal %s.", worker.identifier, channel_id)
            return False

        # Bot: a API proíbe get_dialogs para bots. O caminho é o admin promovê-lo no canal e o bot
        # resolver o canal pelo id (o Telethon pede o access_hash ao Telegram, e funciona para membros).
        admin = self.pool.admin
        if not admin:
            return False
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
        except Exception as exc:
            logging.error("Falha ao promover %s no canal %s: %s", worker.identifier, channel_id, exc)
            return False

        for delay in BOT_VISIBILITY_DELAYS:   # a promoção leva um instante para valer
            await asyncio.sleep(delay)
            if await self._can_see(worker, channel_id):
                return True
        logging.error("O bot %s foi promovido mas ainda não enxerga o canal %s.", worker.identifier, channel_id)
        return False
