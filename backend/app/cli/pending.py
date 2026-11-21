"""Descobre, a partir das filas ``upload_<id>.json``, o que dá para retomar."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.queue_store import QueueStore


@dataclass(frozen=True)
class PendingChannel:
    channel_id: str
    total: int
    sent: int
    root: Path | None        # pasta do curso (para conferir/rescanear)
    is_topics: bool | None   # None = não dá para saber (nada enviado ainda)

    @property
    def remaining(self) -> int:
        return self.total - self.sent


def infer_root(items: list[dict]) -> Path | None:
    """Pasta raiz do curso, a partir do caminho + matéria/subpasta de qualquer item."""
    for item in items:
        full = item.get("full_path")
        if not full:
            continue
        sub = item.get("subfolder") or ""
        if item.get("materia") == "GERAL":
            depth = 1
        else:
            depth = 2 + (len(Path(sub).parts) if sub else 0)
        parents = Path(full).parents
        if depth - 1 < len(parents):
            return parents[depth - 1]
    return None


def list_pending(queue: QueueStore) -> list[PendingChannel]:
    result: list[PendingChannel] = []
    for path in queue.list_files():
        channel_id = path.stem.replace("upload_", "")
        if not channel_id.replace("-", "").isdigit():
            continue
        items = queue.read_file(path)
        if not items:
            continue
        sent = sum(1 for i in items if i.get("sent", False))
        if sent == len(items):
            continue
        topics = True if any(i.get("topic_id") for i in items) else None
        result.append(PendingChannel(channel_id, len(items), sent, infer_root(items), topics))
    return result
