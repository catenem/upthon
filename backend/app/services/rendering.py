"""Textos HTML enviados ao Telegram. Funções puras, fáceis de testar.

Nomes vindos de pastas/arquivos agora passam por ``html.escape`` em todos os
textos (antes só na legenda), evitando mensagens quebradas com '&' ou '<'.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from app.core.config import TELEGRAM_TEXT_LIMIT
from app.utils.text import column_letter, strip_number_prefix, strip_prefix


def _pretty(name: str) -> str:
    return strip_prefix(name).replace("_", " ")


def build_caption(tag: str | None, file_path: str | Path) -> str:
    stem = Path(file_path).stem
    name = _pretty(stem).strip() or stem
    prefix = f"<b>#{tag}</b> - " if tag else ""
    return f"<blockquote>{prefix}<b>{html.escape(name)}</b></blockquote>"


def render_course_summary(items: list[dict]) -> str:
    text = (
        "<blockquote><b>✳️ Clique aqui para ir ao início do curso.</b></blockquote>\n\n"
        "▸ <b>Dica</b>\n"
        "<blockquote><i>Utilize as tags (ex: #M01, #M02) para navegar entre as matérias.</i></blockquote>\n\n"
        "▸ <b>Sumário</b>\n"
        "<blockquote>"
    )
    for i, materia in enumerate(dict.fromkeys(f["materia"] for f in items), 1):
        name = html.escape(_pretty(materia).title())
        text += f"➥ #M{i:02d} - {name}\n"
    return text + "</blockquote>"


def render_topic_index(materia_name: str, folders: list[tuple[str, str]], materia_idx: int) -> str:
    """Índice da matéria. ``folders`` = [(subpasta, letra)]."""
    title = html.escape(_pretty(str(materia_name)).upper())
    text = (
        f"<blockquote><b>❇️ #M{materia_idx:02d}</b></blockquote>\n"
        "<blockquote><b>⚠️ Clique aqui para ir ao início do módulo.</b></blockquote>\n\n"
        f"<b>➥ {title}</b>\n\n"
        "<b>▸ Dica</b>"
        "<blockquote>Utilize as tags (ex: #CC1, #CC2) para navegar entre as aulas.</blockquote>\n\n"
        "<b>▸ Conteúdo</b>"
        "<blockquote>"
    )
    for sub, letter in folders:
        name = html.escape(_pretty(Path(sub).name).title())
        text += f"#{letter}000 - {name}\n\n"
    return text + "</blockquote>"


def render_subfolder_header(subfolder: str | None, tag: str, type_label: str) -> str:
    base = re.split(r"[\\/]", subfolder)[-1] if subfolder else "GERAL"
    name = html.escape(strip_number_prefix(base).replace("_", " ").upper())
    return (
        f"<blockquote><b>#{tag}000</b></blockquote>\n"
        f"<blockquote><b>{name}</b></blockquote>\n\n"
        f"<b>{type_label}</b>\n"
    )


def split_html_message(text: str, limit: int = TELEGRAM_TEXT_LIMIT) -> list[str]:
    """Quebra textos longos em pedaços ≤ ``limit`` preservando ``<blockquote>`` balanceados."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= limit:
            if text.strip():
                chunks.append(text)
            break
        split = text.rfind("\n", 0, limit)
        if split <= 0:  # sem quebra de linha útil (antes: 0 causava loop infinito)
            split = limit
        chunk = text[:split]
        if chunk.count("<blockquote>") > chunk.count("</blockquote>"):
            chunk += "</blockquote>"
            text = "<blockquote>\n" + text[split:]
        else:
            text = text[split:]
        chunks.append(chunk)
    return chunks


__all__ = [
    "build_caption",
    "render_course_summary",
    "render_topic_index",
    "render_subfolder_header",
    "split_html_message",
    "column_letter",
]
