"""Guarda a pasta raiz escolhida (``cli_config.json`` ao lado do banco)."""
from __future__ import annotations

import json
import logging
from pathlib import Path


class CliConfig:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load_root(self) -> Path | None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8")).get("root")
        except (OSError, ValueError):
            return None
        return Path(raw) if raw else None

    def save_root(self, root: Path | None) -> None:
        try:
            self.path.write_text(json.dumps({"root": str(root) if root else None}, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            logging.error("Não foi possível salvar a configuração: %s", exc)
