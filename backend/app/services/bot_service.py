"""Bots trabalhadores: validação do token na Bot API, avatar e persistência.

Segurança: o token do bot NUNCA sai daqui para o front. O avatar é guardado como
``data:`` URI (a URL de arquivo da Bot API contém o token) e a listagem pública
devolve só um ``token_preview`` (o id do bot, que não é segredo).
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import sqlite3

import httpx

from app.core.errors import BadRequest, InternalError, ServiceUnavailable
from app.db.repository import Repository

_API = "https://api.telegram.org"
_LEGACY_AVATAR_PREFIX = f"{_API}/file/bot"  # formato antigo: URL com o token embutido
_MAX_AVATAR_BYTES = 256 * 1024


def token_preview(token: str) -> str:
    """'123456789:AAH...' -> '123456789:…' (só o id público do bot)."""
    bot_id = token.split(":", 1)[0] if ":" in token else token[:4]
    return f"{bot_id}:…"


def public_view(row: dict) -> dict:
    """Campos de um bot que podem ir para o front."""
    avatar = row.get("avatar_url") or ""
    return {
        "id": row["id"],
        "bot_username": row["bot_username"],
        "is_active": row["is_active"],
        # URLs antigas (com token) ficam escondidas até a migração trocá-las por data URI
        "avatar_url": avatar if avatar.startswith("data:") else None,
        "token_preview": token_preview(row["bot_token"]),
    }


class BotService:
    def __init__(self, repo: Repository, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.repo = repo
        self._transport = transport  # injetável nos testes

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=10.0, transport=self._transport)

    async def add_bot(self, token: str) -> str:
        """Valida o token, busca o avatar e grava. Devolve o @username."""
        token = token.strip()
        if not token:
            raise BadRequest("O token não pode estar vazio.")

        try:
            async with self._client() as client:
                info = (await client.get(f"{_API}/bot{token}/getMe")).json()
                if not info.get("ok"):
                    raise BadRequest("Token inválido ou revogado no BotFather.")
                bot_id = info["result"]["id"]
                username = info["result"]["username"]
                try:
                    avatar = await self._fetch_avatar(client, token, bot_id)
                except httpx.RequestError:
                    avatar = ""  # sem avatar não é motivo para recusar o bot
        except httpx.RequestError as exc:
            logging.error("Falha ao comunicar com o Telegram: %s", type(exc).__name__)
            raise ServiceUnavailable(
                "Erro de conexão ao validar o token com os servidores do Telegram."
            ) from exc

        try:
            self.repo.upsert_bot(token, username, avatar)
        except sqlite3.Error as exc:
            logging.error("[DB ERROR] Erro ao guardar bot: %s", exc)
            raise InternalError("Erro ao gravar o bot na base de dados.") from exc
        return username

    @staticmethod
    async def _fetch_avatar(client: httpx.AsyncClient, token: str, bot_id: int) -> str:
        """Baixa a foto do bot e devolve como data URI ('' se não houver foto).

        Levanta ``httpx.RequestError`` em falha de rede: quem chama decide o que fazer.
        """
        photos = (
            await client.get(f"{_API}/bot{token}/getUserProfilePhotos", params={"user_id": bot_id})
        ).json()
        if not (photos.get("ok") and photos["result"]["total_count"] > 0):
            return ""
        file_id = photos["result"]["photos"][0][0]["file_id"]

        info = (await client.get(f"{_API}/bot{token}/getFile", params={"file_id": file_id})).json()
        if not info.get("ok"):
            return ""
        file_path = info["result"]["file_path"]

        resp = await client.get(f"{_API}/file/bot{token}/{file_path}")
        if resp.status_code != 200 or len(resp.content) > _MAX_AVATAR_BYTES:
            return ""
        mime = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(resp.content).decode()}"

    async def refresh_legacy_avatars(self) -> int:
        """Migra avatares antigos (URL com token) para data URI. Best-effort; devolve quantos migrou."""
        try:
            legacy = [
                b for b in self.repo.list_active_bots()
                if (b.get("avatar_url") or "").startswith(_LEGACY_AVATAR_PREFIX)
            ]
        except sqlite3.Error as exc:
            logging.error("Migração de avatares: erro ao ler bots: %s", exc)
            return 0
        if not legacy:
            return 0

        migrated = 0
        async with self._client() as client:
            for bot in legacy:
                try:
                    bot_id = int(bot["bot_token"].split(":", 1)[0])
                    avatar = await self._fetch_avatar(client, bot["bot_token"], bot_id)
                    self.repo.set_avatar(bot["id"], avatar)
                    migrated += 1
                except Exception as exc:  # rede fora do ar: tenta de novo no próximo startup
                    logging.warning("Não consegui migrar o avatar de @%s (%s).", bot["bot_username"], type(exc).__name__)
        logging.info("Avatares de bots migrados: %s/%s", migrated, len(legacy))
        return migrated

    def list_bots(self) -> list[dict]:
        try:
            return [public_view(row) for row in self.repo.list_active_bots()]
        except sqlite3.Error as exc:
            logging.error("Erro ao buscar bots na base de dados: %s", exc)
            raise InternalError("Erro interno ao carregar a lista de bots.") from exc
