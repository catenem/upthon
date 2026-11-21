"""Varredura da pasta do curso e plano de tags (A001, B003...). Puro: sem Telegram."""
from __future__ import annotations

import logging
import os
from itertools import groupby
from pathlib import Path
from typing import TypedDict

from app.core.config import IGNORED_COVER_NAMES, IGNORED_DIRS, IMAGE_EXTS, UPLOAD_VIDEO_EXTS
from app.utils.paths import strip_long_path_prefix, to_long_path
from app.utils.text import column_letter, lead_number, natural_key


class QueueItem(TypedDict, total=False):
    full_path: str
    materia: str
    subfolder: str
    file_name: str
    sent: bool
    topic_id: int
    topic_name: str


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in UPLOAD_VIDEO_EXTS


def scan_folder(folder_path: str | Path) -> list[QueueItem]:
    """Mapeia a pasta em: nível 1 (matéria) > subpastas > arquivos.

    Ordem determinística (natural) para que as tags não dependam do sistema de arquivos.
    Capas genéricas (thumb/cover/capa...) são ignoradas.
    """
    abs_folder = os.path.abspath(folder_path)
    walk_root = str(to_long_path(abs_folder))
    base = Path(strip_long_path_prefix(abs_folder))

    items: list[QueueItem] = []
    for root, dirs, files in os.walk(walk_root):
        dirs[:] = sorted((d for d in dirs if d not in IGNORED_DIRS), key=natural_key)
        for name in sorted(files, key=natural_key):
            p = Path(name)
            if p.stem.lower() in IGNORED_COVER_NAMES and p.suffix.lower() in IMAGE_EXTS:
                continue

            clean_full = strip_long_path_prefix(os.path.join(root, name))
            try:
                parts = Path(clean_full).relative_to(base).parts
            except ValueError as exc:
                logging.error("Falha ao processar ficheiro oculto '%s': %s", name, exc)
                continue

            if len(parts) == 1:
                materia, subfolder = "GERAL", ""
            elif len(parts) == 2:
                materia, subfolder = parts[0], ""
            else:
                materia, subfolder = parts[0], os.path.join(*parts[1:-1])

            items.append(
                {
                    "full_path": clean_full,
                    "materia": materia,
                    "subfolder": subfolder,
                    "file_name": name,
                    "sent": False,
                }
            )
    return items


def order_queue(items: list[QueueItem]) -> list[QueueItem]:
    """Dentro de cada (matéria, subpasta) consecutiva: vídeos primeiro, depois documentos."""
    ordered: list[QueueItem] = []
    for _, group in groupby(items, key=lambda f: (f.get("materia"), f.get("subfolder"))):
        chunk = list(group)
        ordered.extend(f for f in chunk if is_video(f.get("full_path", "")))
        ordered.extend(f for f in chunk if not is_video(f.get("full_path", "")))
    return ordered


def build_tag_plan(items: list[QueueItem]) -> tuple[dict, dict]:
    """Devolve (tag por pasta, tag por arquivo).

    Documentos herdam a tag do vídeo com o mesmo número de prefixo ('03_x.pdf' -> tag de '03_y.mp4').
    """
    folders: dict[tuple, list[QueueItem]] = {}
    for f in items:
        folders.setdefault((f.get("materia"), f.get("subfolder")), []).append(f)

    folder_tags: dict[tuple, str] = {}
    file_tags: dict[str, str] = {}
    for idx, (key, group) in enumerate(folders.items(), 1):
        letter = column_letter(idx)
        folder_tags[key] = letter

        videos = [f for f in group if is_video(f["full_path"])]
        docs = [f for f in group if not is_video(f["full_path"])]

        by_prefix: dict[int, int] = {}
        for n, video in enumerate(videos, 1):
            file_tags[video["full_path"]] = f"{letter}{n:03d}"
            lead = lead_number(os.path.basename(video["full_path"]))
            if lead is not None:
                by_prefix.setdefault(lead, n)

        next_n = len(videos) + 1
        for doc in docs:
            lead = lead_number(os.path.basename(doc["full_path"]))
            if lead is not None and lead in by_prefix:
                n = by_prefix[lead]
            elif len(videos) == 1:
                n = 1
            else:
                n = next_n
                next_n += 1
            file_tags[doc["full_path"]] = f"{letter}{n:03d}"

    return folder_tags, file_tags
