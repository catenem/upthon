"""Estatísticas lidas das filas ``assets/upload_*.json``."""
from __future__ import annotations

import logging

from app.core.config import DASHBOARD_VIDEO_EXTS
from app.core.errors import NotFound
from app.services.queue_store import QueueStore


def _percent(part: int, total: int) -> float:
    return round(part / total * 100, 2) if total > 0 else 0.0


class DashboardService:
    def __init__(self, queue: QueueStore) -> None:
        self.queue = queue

    def pending_channels(self) -> list[str]:
        """Ids (nome do arquivo sem 'upload_') dos canais que ainda têm itens não enviados."""
        pending: list[str] = []
        for path in self.queue.list_files():
            channel_id = path.stem.replace("upload_", "")
            items = self.queue.read_file(path)
            if items is None or not channel_id.replace("-", "").isdigit():
                continue
            if any(item.get("sent", False) is False for item in items):
                pending.append(channel_id)
        return pending

    def _summarize(self, path, include_items: bool = True) -> dict | None:
        items = self.queue.read_file(path)
        if items is None:
            return None

        counts = {"mp4_sent": 0, "mp4_pending": 0, "pdf_sent": 0, "pdf_pending": 0}
        sent_total = 0
        for item in items:
            name = item.get("file_name", "").lower()
            state = "sent" if item.get("sent", False) else "pending"
            sent_total += state == "sent"
            if name.endswith(DASHBOARD_VIDEO_EXTS):
                counts[f"mp4_{state}"] += 1
            elif name.endswith(".pdf"):
                counts[f"pdf_{state}"] += 1

        total = len(items)
        return {
            "channel_id": path.stem.replace("upload_", ""),
            "file_name": path.name,
            "total_items": total,
            "sent_items": sent_total,
            "pending_items": total - sent_total,
            "progress_percentage": _percent(sent_total, total),
            **counts,
            **({"items": items} if include_items else {}),
        }

    def stats(self, include_items: bool = True) -> dict:
        if not self.queue.assets_dir.exists():
            raise NotFound(f"Diretório de assets não encontrado no caminho: {self.queue.assets_dir}")

        channels = [s for p in self.queue.list_files() if (s := self._summarize(p, include_items))]
        total = sum(c["total_items"] for c in channels)
        sent = sum(c["sent_items"] for c in channels)
        logging.debug("Dashboard: %s canais, %s/%s itens", len(channels), sent, total)
        return {
            "total_channels": len(channels),
            "overall_stats": {
                "total_items": total,
                "total_sent": sent,
                "total_pending": sum(c["pending_items"] for c in channels),
                "progress_percentage": _percent(sent, total),
            },
            "channels": channels,
        }

    def items_page(self, channel_id: str, offset: int = 0, limit: int = 100) -> dict:
        """Uma página dos itens de um canal (ou de todos, com ``channel_id='ALL'``)."""
        if not self.queue.assets_dir.exists():
            raise NotFound(f"Diretório de assets não encontrado no caminho: {self.queue.assets_dir}")
        rows: list[dict] = []
        for path in self.queue.list_files():
            cid = path.stem.replace("upload_", "")
            if channel_id != "ALL" and cid != channel_id:
                continue
            items = self.queue.read_file(path)
            if items is None:
                continue
            rows.extend({**item, "channel_id": cid} for item in items)
        return {"total": len(rows), "offset": offset, "items": rows[offset:offset + limit]}
