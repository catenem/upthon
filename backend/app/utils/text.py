"""Helpers puros de texto (sem I/O, sem Telegram)."""
from __future__ import annotations

import re


def natural_key(text: object) -> list:
    """Ordenação natural: 'aula_2' vem antes de 'aula_10'."""
    parts = re.split(r"(\d+)", str(text))
    # re.split com grupo devolve texto nas posições pares e dígitos nas ímpares
    return [int(p) if i % 2 else p.lower() for i, p in enumerate(parts)]


def column_letter(index: int) -> str:
    """1=A, 2=B, 26=Z, 27=AA..."""
    result = ""
    while index > 0:
        index -= 1
        result = chr((index % 26) + 65) + result
        index //= 26
    return result


def strip_prefix(text: str) -> str:
    """Remove números/separadores do início: '01_-_Intro' -> 'Intro'."""
    return re.sub(r"^[\d_.\-\s]+", "", text)


def strip_number_prefix(text: str) -> str:
    """Remove só 'NN_' / 'NN-' / 'NN ' do início (usado no cabeçalho do módulo)."""
    return re.sub(r"^[\d]+[_\-\s]+", "", text)


def lead_number(filename: str) -> int | None:
    m = re.match(r"^\s*(\d+)", filename)
    return int(m.group(1)) if m else None

TOPIC_TITLE_MAX = 128   # limite do Telegram para o título de um tópico

def topic_title(materia: object) -> str:
    """Nome de tópico legível: '02_-_MODULO_01_-_AULAS' -> '02 - MODULO 01 - AULAS'."""
    title = re.sub(r"\s+", " ", str(materia).replace("_", " ")).strip().upper()
    return title[:TOPIC_TITLE_MAX].rstrip()