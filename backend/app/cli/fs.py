"""Navegação em pastas para o terminal (funções puras, fáceis de testar)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config import IGNORED_DIRS, UPLOAD_VIDEO_EXTS
from app.utils.text import natural_key, strip_number_prefix


@dataclass(frozen=True)
class Entry:
    index: int          # 1, 2, 3... (o que o usuário digita)
    name: str           # nome real da pasta
    path: Path
    videos: int
    docs: int
    truncated: bool     # contagem parou no limite (pasta enorme)

    @property
    def label(self) -> str:
        return strip_number_prefix(self.name) or self.name


def count_media(folder: Path, limit: int = 20000) -> tuple[int, int, bool]:
    """(vídeos, outros arquivos, truncado) dentro da pasta, recursivamente, com teto de varredura."""
    videos = docs = seen = 0
    for _root, _dirs, files in os.walk(folder):
        _dirs[:] = [d for d in _dirs if d not in IGNORED_DIRS]
        for name in files:
            seen += 1
            if seen > limit:
                return videos, docs, True
            if Path(name).suffix.lower() in UPLOAD_VIDEO_EXTS:
                videos += 1
            elif Path(name).suffix.lower() == ".pdf":
                docs += 1
    return videos, docs, False


def list_subdirs(folder: Path, *, with_counts: bool = True) -> list[Entry]:
    """Subpastas visíveis em ordem natural, numeradas a partir de 1."""
    try:
        with os.scandir(folder) as it:
            dirs = [e for e in it if e.is_dir() and not e.name.startswith(".")]
    except (PermissionError, FileNotFoundError):
        return []
    dirs.sort(key=lambda e: natural_key(e.name))
    out: list[Entry] = []
    for i, e in enumerate(dirs, start=1):
        v, d, cut = count_media(Path(e.path)) if with_counts else (0, 0, False)
        out.append(Entry(i, e.name, Path(e.path), v, d, cut))
    return out


def parent_within(current: Path, root: Path | None) -> Path | None:
    """Pasta acima de `current`; None se já está na raiz fixa (ou no topo do disco)."""
    if root is not None and current.resolve() == root.resolve():
        return None
    parent = current.parent
    return None if parent == current else parent


def resolve_index(entries: list[Entry], raw: str) -> Entry | None:
    raw = raw.strip()
    if not raw.isdigit():
        return None
    n = int(raw)
    return entries[n - 1] if 1 <= n <= len(entries) else None
