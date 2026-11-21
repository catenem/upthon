"""Entrada/saída do terminal atrás de uma interface pequena (nos testes entra uma versão falsa)."""
from __future__ import annotations

import asyncio
import getpass


class Console:
    def say(self, text: str = "") -> None:
        print(text)

    async def ask(self, prompt: str) -> str:
        # em thread: o loop do asyncio (e o keep-alive do Telethon) continua vivo enquanto se digita
        try:
            return (await asyncio.to_thread(input, prompt)).strip()
        except EOFError:
            return "q"

    async def ask_secret(self, prompt: str) -> str:
        return await asyncio.to_thread(getpass.getpass, prompt)

    async def confirm(self, prompt: str, default: bool = False) -> bool:
        hint = "S/n" if default else "s/N"
        answer = (await self.ask(f"{prompt} [{hint}] ")).lower()
        if not answer:
            return default
        return answer in ("s", "sim", "y", "yes")
