"""Helpers de caminho, incluindo o prefixo de caminho longo do Windows (``\\\\?\\``)."""
from __future__ import annotations

import os
from pathlib import Path

_LONG_PREFIX = "\\\\?\\"
_JUNK_PREFIXES = ("\\\\?\\", "\\?\\", "\\\\?/", "\\?/")


def to_long_path(path: str | Path) -> Path:
    """No Windows adiciona ``\\\\?\\`` para suportar caminhos > 260 caracteres."""
    p = str(path)
    if os.name == "nt" and not p.startswith(_LONG_PREFIX):
        return Path(f"{_LONG_PREFIX}{p}")
    return Path(p)


def strip_long_path_prefix(path: str) -> str:
    return path.replace(_LONG_PREFIX, "")


def clean_path(raw_path: object) -> str:
    """Normaliza caminhos vindos do JSON/frontend (prefixos do Windows, ``\\/``)."""
    if not raw_path:
        return raw_path  # type: ignore[return-value]
    s = str(raw_path)
    for junk in _JUNK_PREFIXES:
        s = s.replace(junk, "")
    s = s.replace("\\/", "/")
    if os.name != "nt" and not s.startswith("/") and s.startswith("media/"):
        s = "/" + s
    return s
