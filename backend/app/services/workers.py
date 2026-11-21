"""Workers (conta admin + bots): só transporte de rede, sem regra de negócio."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from telethon import TelegramClient, errors, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

from app.core.config import VIDEO_ATTRIBUTE_EXTS, Settings
from app.db.repository import Repository
from app.services import media
from app.services.rendering import build_caption, split_html_message
from app.services.scanner import QueueItem
from app.services.telegram_session import TelegramSession
from app.utils.paths import clean_path


@dataclass(frozen=True)
class SendResult:
    """Substitui o retorno misto True/False/int (segundos de FloodWait) do código antigo."""

    ok: bool
    flood_wait: int | None = None


OK = SendResult(True)
FAILED = SendResult(False)


def flooded(seconds: int) -> SendResult:
    return SendResult(False, flood_wait=int(seconds))


@dataclass
class PendingDoc:
    file: Any                # handle devolvido pelo upload (pertence ao cliente que enviou)
    caption: str
    client: TelegramClient
    item: QueueItem


class TelegramWorker:
    def __init__(
        self,
        client: TelegramClient,
        identifier: str,
        *,
        is_bot: bool = False,
        default_thumbnail: Path | None = None,
    ) -> None:
        self.client = client
        self.identifier = identifier
        self.is_bot = is_bot
        self.default_thumbnail = default_thumbnail

    async def send_video(
        self,
        chat_id: int,
        video_path: str,
        *,
        reply_to: int | None = None,
        tag: str | None = None,
        thumbnail: str | None = None,
    ) -> SendResult:
        try:
            prepared = await media.prepare_video(video_path, thumbnail, self.default_thumbnail)
            if prepared is None:
                return FAILED

            attributes = []
            if prepared.path.lower().endswith(VIDEO_ATTRIBUTE_EXTS):
                attributes = [
                    types.DocumentAttributeVideo(
                        duration=prepared.duration,
                        w=prepared.width,
                        h=prepared.height,
                        round_message=False,
                        supports_streaming=True,
                    )
                ]
            await self.client.send_file(
                chat_id,
                file=prepared.path,
                thumb=prepared.thumb,
                caption=build_caption(tag, clean_path(video_path)),
                parse_mode="html",
                reply_to=reply_to,
                attributes=attributes,
            )
            return OK
        except errors.FloodWaitError as exc:
            logging.warning("FloodWait: aguarde %ss", exc.seconds)
            return flooded(exc.seconds)
        except Exception:
            logging.exception("Erro ao enviar vídeo %s", video_path)
            return FAILED

    async def send_text(self, chat_id: int, text: str, *, reply_to: int | None = None) -> SendResult:
        try:
            for i, chunk in enumerate(split_html_message(str(text))):
                if i:
                    await asyncio.sleep(1.5)
                await self.client.send_message(chat_id, chunk, parse_mode="html", reply_to=reply_to)
            return OK
        except errors.FloodWaitError as exc:
            return flooded(exc.seconds)
        except Exception:
            logging.exception("Erro ao enviar mensagem de texto para %s", chat_id)
            return FAILED

    async def send_summary(
        self, chat_id: int, text: str, *, file_path: str | None = None, reply_to: int | None = None
    ) -> SendResult:
        """Imagem + sumário; se a legenda passar de 1024 caracteres, envia em duas mensagens."""
        try:
            if file_path and str(file_path).lower() not in ("none", "null", ""):
                if len(text) <= 1024:
                    await self.client.send_file(
                        chat_id, file=str(file_path), caption=text, parse_mode="html", reply_to=reply_to
                    )
                else:
                    await self.client.send_file(chat_id, file=str(file_path), reply_to=reply_to)
                    await self.send_text(chat_id, text, reply_to=reply_to)
            else:
                await self.send_text(chat_id, text, reply_to=reply_to)
            return OK
        except errors.FloodWaitError as exc:
            return flooded(exc.seconds)
        except Exception:
            logging.exception("Erro ao transmitir sumário global")
            return FAILED

    async def send_sticker(
        self, chat_id: int, sticker_set: str, index: int = 0, *, reply_to: int | None = None
    ) -> SendResult:
        try:
            result = await self.client(
                GetStickerSetRequest(stickerset=InputStickerSetShortName(short_name=sticker_set), hash=0)
            )
            await self.client.send_file(chat_id, result.documents[index], reply_to=reply_to)
            return OK
        except Exception:
            logging.exception("Erro ao enviar sticker do set %s", sticker_set)
            return FAILED


async def send_grouped_docs(chat_id: int, docs: list[PendingDoc], *, reply_to: int | None = None) -> list[PendingDoc]:
    """Envia documentos em álbuns, agrupando por cliente (o handle só vale para quem fez o upload).

    Devolve apenas os documentos que realmente foram enviados, para o chamador marcá-los
    como concluídos (antes eram marcados ao entrar no buffer, mesmo sem terem sido enviados).
    """
    if not docs:
        return []

    batches: list[list[PendingDoc]] = []
    for doc in docs:
        if batches and batches[-1][0].client is doc.client:
            batches[-1].append(doc)
        else:
            batches.append([doc])

    sent: list[PendingDoc] = []
    for batch in batches:
        client = batch[0].client
        files = [d.file for d in batch]
        captions = [d.caption for d in batch]
        try:
            await client.send_file(
                chat_id,
                file=files if len(files) > 1 else files[0],
                caption=captions if len(files) > 1 else captions[0],
                parse_mode="html",
                reply_to=reply_to,
            )
            sent.extend(batch)
            await asyncio.sleep(1)
        except Exception as exc:
            logging.warning("Erro ao enviar lote agrupado: %s. Desmontando para envio individual...", exc)
            for doc in batch:
                try:
                    await client.send_file(
                        chat_id, file=doc.file, caption=doc.caption, parse_mode="html", reply_to=reply_to
                    )
                    sent.append(doc)
                    await asyncio.sleep(0.5)
                except Exception as ind_err:
                    logging.error("Falha ao enviar %s individualmente: %s", doc.item.get("file_name"), ind_err)
    return sent


class WorkerPool:
    """Conjunto de workers: a conta admin (usuário) mais os bots ativos."""

    def __init__(self, session: TelegramSession, repo: Repository, settings: Settings) -> None:
        self.session = session
        self.repo = repo
        self.settings = settings
        self.workers: list[TelegramWorker] = []

    @property
    def admin(self) -> TelegramWorker | None:
        return next((w for w in self.workers if not w.is_bot), None)

    def active(self, *, only_bots: bool = False) -> list[TelegramWorker]:
        return [w for w in self.workers if w.is_bot] if only_bots else list(self.workers)

    async def setup(self) -> bool:
        """(Re)constrói a lista de workers. Devolve True se há ao menos um."""
        await self.shutdown_bots()
        self.workers = []

        credentials = self.repo.get_credentials()
        client = self.session.client
        if client and self.session.authorized:
            try:
                if await client.is_user_authorized():
                    self.workers.append(
                        TelegramWorker(
                            client,
                            (credentials or {}).get("phone", "Admin"),
                            default_thumbnail=self.settings.default_thumbnail,
                        )
                    )
            except Exception as exc:
                logging.error("Erro ao vincular cliente Admin aos workers: %s", exc)

        if not credentials:
            logging.error("Não foi possível carregar Bots: nenhuma credencial api_id/api_hash no banco.")
            return bool(self.workers)

        for bot in self.repo.list_active_bots():
            try:
                bot_client = TelegramClient(
                    StringSession(""), int(credentials["api_id"]), str(credentials["api_hash"])
                )
                await bot_client.start(bot_token=bot["bot_token"])
                self.workers.append(
                    TelegramWorker(
                        bot_client,
                        bot["bot_username"],
                        is_bot=True,
                        default_thumbnail=self.settings.default_thumbnail,
                    )
                )
            except errors.FloodWaitError as exc:
                logging.warning(
                    "O Bot %s está em FloodWait: %ss (~%s min).", bot["bot_username"], exc.seconds, exc.seconds // 60
                )
            except Exception as exc:
                logging.error("Erro inesperado ao iniciar o Bot %s: %s", bot["bot_username"], exc)
        return bool(self.workers)

    async def shutdown_bots(self) -> None:
        """Desconecta os clientes dos bots (antes nunca eram desconectados)."""
        for worker in self.workers:
            if worker.is_bot:
                try:
                    await worker.client.disconnect()
                except Exception as exc:
                    logging.error("Erro ao desconectar bot %s: %s", worker.identifier, exc)
