"""Fila de upload persistida em ``assets/upload_<channel_id>.json`` (formato inalterado).

A gravação agora é atômica (arquivo temporário + ``os.replace``): queda de energia
no meio da escrita não corrompe mais o JSON de retomada.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.services.scanner import QueueItem


class QueueStore:
    def __init__(self, assets_dir: Path) -> None:
        self.assets_dir = Path(assets_dir)

    def path_for(self, channel_id: int | str) -> Path:
        return self.assets_dir / f"upload_{channel_id}.json"

    def exists(self, channel_id: int | str) -> bool:
        return self.path_for(channel_id).exists()

    def list_files(self) -> list[Path]:
        return sorted(self.assets_dir.glob("upload_*.json"))

    def load(self, channel_id: int | str) -> list[QueueItem]:
        path = self.path_for(channel_id)
        if not path.exists():
            return []
        return self.read_file(path) or []

    @staticmethod
    def read_file(path: Path) -> list[QueueItem] | None:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logging.error("Erro ao ler a fila do JSON (%s): %s", path.name, exc)
            return None

    def save(self, channel_id: int | str, items: list[QueueItem]) -> None:
        if not channel_id:
            logging.error("Erro: channel_id inválido para salvar a fila.")
            return
        path = self.path_for(channel_id)
        try:
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump([_serializable(i) for i in items], fh, indent=4, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception as exc:
            logging.error("Erro ao salvar a fila no JSON (%s): %s", path.name, exc)

    def mark_sent(self, channel_id: int | str, items: list[QueueItem], sent: list[QueueItem]) -> None:
        """Marca vários itens como enviados e grava UMA vez."""
        if not sent:
            return
        for item in sent:
            item["sent"] = True
        self.save(channel_id, items)

    @staticmethod
    def stamp_topic(items: list[QueueItem], materia: str, topic_id: int, topic_name: str | None = None) -> bool:
        """Grava id (e nome) do tópico em todos os itens da matéria. True se algo mudou."""
        changed = False
        for item in items:
            if item.get("materia") != materia:
                continue
            if item.get("topic_id") != topic_id:
                item["topic_id"] = topic_id
                changed = True
            if topic_name is not None and item.get("topic_name") != topic_name:
                item["topic_name"] = topic_name
                changed = True
        return changed


def _serializable(item: QueueItem) -> dict:
    out = dict(item)
    if isinstance(out.get("full_path"), Path):
        out["full_path"] = str(out["full_path"])
    return out
