"""Sessão da conta admin no Telegram: auto-login, login por código/2FA e perfil.

Reúne o que antes estava espalhado entre ``main.py`` (rotas de login com lógica
Telethon dentro), ``TelegramModel`` e ``UserClient`` (que nunca era usado).
"""
from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.sessions import StringSession

from app.core.errors import BadRequest, NotFound, RateLimited, Unauthorized
from app.db.repository import Repository


@dataclass(frozen=True)
class VerifyResult:
    needs_password: bool
    session: str | None = None


class TelegramSession:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        self.client: TelegramClient | None = None
        self.authorized = False
        self._code_hashes: dict[str, str] = {}

    # --- auto-login -------------------------------------------------------------
    async def restore(self) -> bool:
        creds = self.repo.get_credentials()
        if not creds:
            logging.warning("[AUTO-LOGIN] Nenhuma credencial encontrada na tabela 'settings'.")
            return False
        if not creds.get("session_str"):
            logging.warning("[AUTO-LOGIN] Telefone %s encontrado, mas 'session_str' está vazia.", creds.get("phone"))
            return False
        try:
            client = TelegramClient(
                StringSession(creds["session_str"]), int(creds["api_id"]), str(creds["api_hash"])
            )
            await client.connect()
            if await client.is_user_authorized():
                self.client, self.authorized = client, True
                return True
            logging.warning("[AUTO-LOGIN] Sessão expirada: o Telegram rejeitou a session_str.")
            await client.disconnect()
            return False
        except Exception as exc:
            logging.error("[AUTO-LOGIN] Falha ao inicializar Telethon: %s", exc)
            return False

    # --- login por código -------------------------------------------------------
    @staticmethod
    def _validate_api_id(raw: str) -> int:
        try:
            value = int(raw)
            if not (-2147483648 <= value <= 2147483647):
                raise ValueError(f"O api_id '{value}' é inválido. Verifica as credenciais.")
            return value
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc

    async def request_code(self, api_id: str, api_hash: str, phone: str) -> None:
        api_id_int = self._validate_api_id(api_id)
        try:
            self.repo.save_credentials(api_id_int, api_hash, phone)

            if self.client:  # evita deixar o cliente anterior conectado e órfão
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            self.authorized = False
            self.client = TelegramClient(StringSession(), api_id_int, api_hash)

            logging.info("A iniciar a ligacao ao Telegram...")
            await self.client.connect()
            result = await self.client.send_code_request(phone)
            self._code_hashes[phone] = result.phone_code_hash
            logging.info("Login solicitado. Código enviado.")
        except FloodWaitError as exc:
            logging.warning("Limite do Telegram atingido. Aguardar %s segundos.", exc.seconds)
            raise RateLimited(
                {
                    "erro": "Muitas tentativas. O Telegram bloqueou temporariamente o envio de SMS.",
                    "segundos_espera": exc.seconds,
                    "minutos_espera": round(exc.seconds / 60, 1),
                }
            ) from exc
        except Exception as exc:
            logging.error("Erro geral no login: %s", exc)
            raise BadRequest(f"Erro de ligacao com o Telegram: {exc}") from exc

    async def verify_code(self, phone: str, code: str, password: str | None) -> VerifyResult:
        code_hash = self._code_hashes.get(phone)
        if not code_hash or not self.client:
            raise NotFound("Sessão expirada ou não encontrada. Solicite o código novamente.")
        try:
            try:
                await self.client.sign_in(phone=phone, code=code, phone_code_hash=code_hash)
            except SessionPasswordNeededError:
                if not password:
                    return VerifyResult(needs_password=True)
                await self.client.sign_in(password=password)

            session_str = self.client.session.save()
            self.repo.update_session_string(phone, session_str)
            self.authorized = True
            del self._code_hashes[phone]
            return VerifyResult(needs_password=False, session=session_str)
        except Exception as exc:
            logging.error("Erro na verificacao do codigo: %s", exc)
            raise BadRequest(str(exc)) from exc

    # --- perfil -----------------------------------------------------------------
    async def current_user(self) -> dict:
        if not self.client or not self.authorized:
            raise Unauthorized("Não conectado")
        me = await self.client.get_me()
        return {"name": me.first_name, "photo": await self.profile_photo_base64()}

    async def profile_photo_base64(self) -> str | None:
        if not self.client or not self.authorized:
            return None
        try:
            buffer = io.BytesIO()
            await self.client.download_profile_photo("me", file=buffer)
            if buffer.tell() == 0:  # usuário sem foto
                return None
            buffer.seek(0)
            return f"data:image/jpeg;base64,{base64.b64encode(buffer.read()).decode()}"
        except Exception as exc:
            logging.error("Erro ao obter foto de perfil: %s", exc)
            return None

    async def disconnect(self) -> None:
        if self.client:
            try:
                await self.client.disconnect()
                logging.info("Sessão do Telegram desconectada com segurança.")
            except Exception as exc:
                logging.error("Erro ao desconectar cliente: %s", exc)
