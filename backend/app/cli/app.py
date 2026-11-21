"""Menu interativo: navegar pastas, upar por índice e retomar uploads pendentes."""
from __future__ import annotations

import logging
from pathlib import Path

from app.cli.console import Console
from app.cli.fs import Entry, count_media, list_subdirs, parent_within, resolve_index
from app.cli.pending import PendingChannel, list_pending
from app.cli.settings_store import CliConfig
from app.core.errors import UpthonError
from app.utils.text import strip_number_prefix

HELP = (
    "  <n>        upar a pasta de índice n        a <n>   abrir a pasta n\n"
    "  ..         voltar                          r       ir para a pasta raiz\n"
    "  u          upar a pasta atual              d       definir pasta raiz (fixa)\n"
    "  p          uploads pendentes               q       sair"
)


class CliApp:
    def __init__(self, container, console: Console, config: CliConfig, start: Path | None = None) -> None:
        self.c = container
        self.io = console
        self.config = config
        self.root: Path | None = start or config.load_root()
        self.current: Path = self.root or Path.home()

    # ------------------------------------------------------------------ navegação
    async def run(self) -> None:
        self.io.say("=== Upthon CLI ===")
        while True:
            entries = list_subdirs(self.current)
            self._render(entries)
            cmd = await self.io.ask("> ")
            if not await self._dispatch(cmd, entries):
                return

    def _render(self, entries: list[Entry]) -> None:
        fixed = f"  (raiz fixa: {self.root})" if self.root else "  (sem raiz fixa: use 'd' para definir)"
        self.io.say(f"\n📁 {self.current}{fixed}")
        if not entries:
            self.io.say("   (nenhuma subpasta aqui; use 'u' para upar esta pasta ou '..' para voltar)")
        width = len(str(len(entries)))
        for e in entries:
            more = "+" if e.truncated else ""
            self.io.say(f"  [{e.index:>{width}}] {e.name}   {e.videos}{more} vídeos · {e.docs}{more} pdfs")
        self.io.say("\n" + HELP)

    async def _dispatch(self, cmd: str, entries: list[Entry]) -> bool:
        low = cmd.lower()
        if low in ("q", "sair", "exit"):
            return False
        if low in ("", "?", "h", "ajuda"):
            return True
        if low == "..":
            up = parent_within(self.current, self.root)
            if up is None:
                self.io.say("Você já está na pasta raiz.")
            else:
                self.current = up
        elif low == "r":
            self.current = self.root or Path.home()
        elif low == "d":
            await self._set_root()
        elif low == "p":
            await self.pending_menu()
        elif low == "u":
            await self.upload_flow(self.current)
        elif low.startswith("a ") or low.startswith("cd "):
            target = resolve_index(entries, cmd.split(maxsplit=1)[1])
            if target is None:
                self.io.say("Índice inválido.")
            else:
                self.current = target.path
        else:
            target = resolve_index(entries, cmd)
            if target is None:
                self.io.say("Comando não reconhecido. Digite um índice ou veja os comandos acima.")
            else:
                await self.upload_flow(target.path)
        return True

    async def _set_root(self) -> None:
        raw = await self.io.ask("Caminho da pasta raiz (vazio = pasta atual): ")
        path = Path(raw).expanduser() if raw else self.current
        if not path.is_dir():
            self.io.say(f"Pasta não encontrada: {path}")
            return
        self.root = path.resolve()
        self.current = self.root
        self.config.save_root(self.root)
        self.io.say(f"Raiz salva: {self.root}")

    # ------------------------------------------------------------------ upload novo
    async def upload_flow(self, folder: Path) -> None:
        videos, docs, cut = count_media(folder)
        if videos + docs == 0:
            self.io.say("Nada para enviar nessa pasta (nenhum vídeo ou PDF).")
            return
        self.io.say(f"\nPasta: {folder}\n  {videos}{'+' if cut else ''} vídeos · {docs}{'+' if cut else ''} pdfs")

        is_topics = await self._ask_channel_type()
        if is_topics is None:
            return
        default_name = strip_number_prefix(folder.name) or folder.name
        name = await self.io.ask(f"Nome do canal [{default_name}]: ") or default_name
        kind = "supergrupo com tópicos" if is_topics else "canal privado"
        if not await self.io.confirm(f"Criar {kind} '{name}' e enviar {folder.name}?"):
            self.io.say("Cancelado.")
            return
        if not await self._ensure_ready():
            return

        try:
            channel_id = await self.c.channels.create_channel(name, is_topic=is_topics)
            self.io.say(f"Canal criado (id {channel_id}). Enviando... (Ctrl+C interrompe; retome em 'p')")
            await self.c.uploads.upload(str(folder), channel_id, is_topics)
            self.io.say("Upload finalizado.")
        except UpthonError as exc:
            self.io.say(f"Erro: {exc.detail}")
        except Exception as exc:  # noqa: BLE001 - o menu não pode cair por um upload
            logging.exception("Falha no upload")
            self.io.say(f"Erro: {exc}")

    async def _ask_channel_type(self) -> bool | None:
        self.io.say("\nTipo do canal:\n  [1] Canal privado\n  [2] Supergrupo (com tópicos)\n  [0] Cancelar")
        while True:
            a = await self.io.ask("Tipo: ")
            if a == "1":
                return False
            if a == "2":
                return True
            if a in ("0", "q", ""):
                return None
            self.io.say("Digite 1, 2 ou 0.")

    # ------------------------------------------------------------------ pendentes
    async def pending_menu(self) -> None:
        pendings = list_pending(self.c.queue)
        if not pendings:
            self.io.say("\nNenhum upload pendente. 🎉")
            return
        self.io.say("\nUploads pendentes:")
        for i, p in enumerate(pendings, start=1):
            where = p.root.name if p.root else "pasta desconhecida"
            kind = {True: "tópicos", None: "tipo ?"}[p.is_topics]
            self.io.say(f"  [{i}] canal {p.channel_id}  {p.sent}/{p.total} enviados  ({p.remaining} faltam)  {where}  [{kind}]")
        a = await self.io.ask("Índice para retomar (vazio = voltar): ")
        if not a.isdigit() or not 1 <= int(a) <= len(pendings):
            return
        await self.resume_flow(pendings[int(a) - 1])

    async def resume_flow(self, p: PendingChannel) -> None:
        is_topics = p.is_topics
        if is_topics is None:
            is_topics = await self._ask_channel_type()
            if is_topics is None:
                return
        if not await self.io.confirm(f"Retomar o canal {p.channel_id} ({p.remaining} itens faltando)?", default=True):
            return
        if not await self._ensure_ready():
            return
        folder = str(p.root) if p.root else ""
        try:
            self.io.say("Retomando... (Ctrl+C interrompe; retome de novo em 'p')")
            await self.c.uploads.upload(folder, p.channel_id, is_topics)
            self.io.say("Retomada finalizada.")
        except UpthonError as exc:
            self.io.say(f"Erro: {exc.detail}")
        except Exception as exc:  # noqa: BLE001
            logging.exception("Falha ao retomar")
            self.io.say(f"Erro: {exc}")

    # ------------------------------------------------------------------ login
    async def _ensure_ready(self) -> bool:
        if not self.c.is_authorized and not await self._login():
            return False
        if not await self.c.uploads.ensure_workers():
            self.io.say("Nenhuma conta (admin ou bot) disponível para enviar.")
            return False
        return True

    async def _login(self) -> bool:
        self.io.say("\nVocê ainda não está logado no Telegram.")
        creds = self.c.repo.get_credentials() or {}
        api_id = await self.io.ask(f"api_id [{creds.get('api_id', '')}]: ") or str(creds.get("api_id", ""))
        api_hash = await self.io.ask("api_hash [Enter = o salvo]: ") or str(creds.get("api_hash", ""))
        phone = await self.io.ask(f"Telefone com DDI, ex. +5511999999999 [{creds.get('phone', '')}]: ") or str(
            creds.get("phone", "")
        )
        try:
            await self.c.session.request_code(api_id, api_hash, phone)
            code = await self.io.ask("Código recebido no Telegram: ")
            result = await self.c.session.verify_code(phone, code, None)
            if result.needs_password:
                pwd = await self.io.ask_secret("Senha de duas etapas: ")
                result = await self.c.session.verify_code(phone, code, pwd)
        except UpthonError as exc:
            self.io.say(f"Erro no login: {exc.detail}")
            return False
        if not self.c.is_authorized:
            self.io.say("Login não concluído.")
            return False
        await self.c.pool.setup()
        self.io.say("Login feito.")
        return True
