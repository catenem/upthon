"""Orquestração do upload de um curso para um canal.

Substitui o método ``UpthonController.upload`` (~270 linhas) por uma classe de estado
(`_UploadRun`) com um método por decisão: entrar em matéria, entrar em subpasta,
cabeçalho, enviar vídeo, enfileirar documento, descarregar álbum.
"""
from __future__ import annotations

import asyncio
import logging

from app.utils.text import topic_title
from app.core.config import DOC_ALBUM_SIZE, Settings
from app.services import media
from app.services.channels import ChannelService, normalize_channel_id
from app.services.queue_store import QueueStore
from app.services.rendering import (
    build_caption,
    render_course_summary,
    render_subfolder_header,
    render_topic_index,
)
from app.services.scanner import QueueItem, build_tag_plan, is_temp_artifact, is_video, order_queue, scan_folder
from app.services.workers import PendingDoc, TelegramWorker, WorkerPool, send_grouped_docs

_UNSET = object()


class TopicUnavailable(RuntimeError):
    """Não há tópico para a matéria atual; o upload para e pode ser retomado depois."""


class UploadService:
    def __init__(self, pool: WorkerPool, channels: ChannelService, queue: QueueStore, settings: Settings) -> None:
        self.pool = pool
        self.channels = channels
        self.queue = queue
        self.settings = settings
        self._running: set[int] = set()

    async def ensure_workers(self) -> bool:
        """Inicialização tardia: cobre o caso de login feito depois do startup."""
        if self.pool.workers:
            return True
        logging.info("Fila de workers vazia. Tentando inicialização tardia...")
        return await self.pool.setup()

    def is_running(self, channel_id: object) -> bool:
        return normalize_channel_id(channel_id) in self._running

    async def run_job(self, path: str, channel_id: int | str, is_topics: bool) -> None:
        """Wrapper para BackgroundTasks: nunca deixa a exceção vazar."""
        try:
            logging.info("[TASK] Upload iniciado (canal %s)...", channel_id)
            await self.upload(path, channel_id, is_topics)
            logging.info("[TASK] Upload finalizado (canal %s).", channel_id)
        except Exception:
            logging.exception("[TASK] ERRO FATAL NO UPLOAD (canal %s)", channel_id)

    async def upload(self, path: str, channel_id: int | str, is_topics: bool = False, only_bots: bool = False) -> None:
        cid = normalize_channel_id(channel_id)
        if cid is None:
            logging.error("O identificador '%s' não é um ID numérico válido.", channel_id)
            return
        workers = self.pool.active(only_bots=only_bots)
        if not workers:
            logging.error("Nenhuma conta disponível para realizar o upload.")
            return
        if cid in self._running:
            logging.warning("Já existe um upload em andamento para o canal %s.", cid)
            return

        self._running.add(cid)
        try:
            await self._upload(path, cid, workers, is_topics)
        finally:
            self._running.discard(cid)

    # ------------------------------------------------------------------------
    async def _upload(self, path: str, cid: int, workers: list[TelegramWorker], is_topics: bool) -> None:
        items = self._load_or_scan(path, cid)
        if not items:
            return
        if not is_topics and any(i.get("topic_id") for i in items):
            # A fila já tem tópicos: o canal é um fórum, mesmo que quem retomou tenha esquecido de avisar.
            logging.info("Fila com tópicos detectada: retomando como supergrupo com tópicos.")
            is_topics = True
        if not await self.channels.ensure_access(workers, cid):
            return

        run = _UploadRun(self, workers, cid, order_queue(items), is_topics)
        if is_topics:
            await run.map_topics()   # antes de enviar qualquer coisa: se falhar, nada saiu
        await self._send_intro(path, cid, workers[0], items)
        await run.run()

    def _load_or_scan(self, path: str, cid: int) -> list[QueueItem]:
        if self.queue.exists(cid):
            items = self.queue.load(cid)
            kept = [i for i in items if not is_temp_artifact(i.get("file_name") or i.get("full_path") or "")]
            if len(kept) != len(items):
                # filas criadas antes continham sobras do ffmpeg (_ready.mp4) que somem durante o envio
                logging.warning("Removidas %d sobras de conversão (_ready.mp4) da fila.", len(items) - len(kept))
                self.queue.save(cid, kept)
            return kept
        scanned = scan_folder(path)
        self.queue.save(cid, scanned)
        return scanned

    async def _send_intro(self, path: str, cid: int, worker: TelegramWorker, items: list[QueueItem]) -> None:
        """Sumário + separador, só na primeira execução (nada enviado ainda)."""
        if any(i.get("sent", False) for i in items):
            return
        await worker.send_summary(
            cid, render_course_summary(items), file_path=media.find_summary_thumbnail(path)
        )
        await worker.send_sticker(cid, self.settings.separator_sticker_set, 1)


class _UploadRun:
    """Estado de uma execução de upload (posição atual, álbum pendente, rodízio de workers)."""

    def __init__(
        self, svc: UploadService, workers: list[TelegramWorker], channel_id: int, items: list[QueueItem], is_topics: bool
    ) -> None:
        self.svc = svc
        self.workers = workers
        self.channel_id = channel_id
        self.items = items
        self.is_topics = is_topics

        self.worker_idx = 0
        self.docs: list[PendingDoc] = []
        self.reply_to: int | None = None
        self.current_materia: object = _UNSET
        self.current_subfolder: object = _UNSET
        self.videos_header_sent = False
        self.docs_header_sent = False

        self.folder_tags, self.file_tags = build_tag_plan(items)
        self.materias = list(dict.fromkeys(i["materia"] for i in items))

    @property
    def worker(self) -> TelegramWorker:
        return self.workers[self.worker_idx]

    def rotate(self) -> None:
        self.worker_idx = (self.worker_idx + 1) % len(self.workers)

    async def run(self) -> None:
        for item in self.items:
            if item.get("full_path") is None:
                continue
            is_sent = item.get("sent", False)

            if item.get("materia") != self.current_materia:
                await self._enter_materia(item, is_sent)
            if item.get("subfolder") != self.current_subfolder:
                await self._enter_subfolder(item, is_sent)
            if is_sent:
                continue

            await self._send_header_if_needed(item)
            await self._send_item(item)

        await self._flush_docs()

    # --- tópicos --------------------------------------------------------------
    async def map_topics(self) -> None:
        """Garante um tópico (id + nome gravados na fila) para cada matéria que ainda tem algo a enviar.

        Roda antes de enviar qualquer coisa, então a fila vira o mapa matéria -> tópico. Na retomada,
        matérias sem id (fila antiga, falha anterior) ganham o tópico aqui, nunca vão para o General.
        """
        for materia in self.materias:
            group = [i for i in self.items if i.get("materia") == materia]
            if not materia or all(i.get("sent", False) for i in group):
                continue
            if all(i.get("topic_id") for i in group):
                continue
            title = topic_title(materia)
            topic_id = await self.svc.channels.get_or_create_topic(self.channel_id, title)
            if not topic_id:
                raise TopicUnavailable(f"Não foi possível criar/obter o tópico da matéria '{materia}'.")
            self.svc.queue.stamp_topic(self.items, materia, topic_id, title)
            self.svc.queue.save(self.channel_id, self.items)

    # --- transições -----------------------------------------------------------
    async def _enter_materia(self, item: QueueItem, is_sent: bool) -> None:
        await self._flush_docs()
        materia = item.get("materia")

        # O id vem do mapa gravado na fila (_map_topics). Matéria 100% enviada não tem tópico novo: ok.
        self.reply_to = item.get("topic_id") or None
        if self.is_topics and not self.reply_to and not is_sent:
            # Nunca cair no General por engano: para aqui e deixa a fila intacta para retomar.
            raise TopicUnavailable(f"Matéria '{materia}' sem tópico; envio interrompido para não ir ao General.")

        if not is_sent:
            folders = [
                (sub, self.folder_tags[(materia, sub)])
                for sub in dict.fromkeys(
                    f["subfolder"] for f in self.items if f["materia"] == materia and f["subfolder"]
                )
            ]
            text = render_topic_index(materia, folders, self.materias.index(materia) + 1)
            await self.worker.send_text(self.channel_id, text, reply_to=self.reply_to)

        self.current_materia = materia
        self.current_subfolder = _UNSET

    async def _enter_subfolder(self, item: QueueItem, is_sent: bool) -> None:
        self.videos_header_sent = False
        self.docs_header_sent = False
        await self._flush_docs()
        if not is_sent:
            await self.worker.send_sticker(
                self.channel_id, self.svc.settings.separator_sticker_set, 1, reply_to=self.reply_to
            )
        self.current_subfolder = item.get("subfolder")

    async def _send_header_if_needed(self, item: QueueItem) -> None:
        video = is_video(item["full_path"])
        if video and not self.videos_header_sent:
            label, self.videos_header_sent = "▶️ Vídeo aulas abaixo", True
        elif not video and not self.docs_header_sent:
            label, self.docs_header_sent = "♻️ Materiais de apoio abaixo", True
        else:
            return
        tag = self.folder_tags.get((item.get("materia"), item.get("subfolder")))
        header = render_subfolder_header(item.get("subfolder"), tag, label)
        await self.worker.send_text(self.channel_id, header, reply_to=self.reply_to)
        await asyncio.sleep(0.5)

    # --- envio ----------------------------------------------------------------
    async def _send_item(self, item: QueueItem) -> None:
        path = item["full_path"]
        tag = self.file_tags.get(path)
        ok = await (self._send_video(item, tag) if is_video(path) else self._queue_doc(item, tag))
        if not ok:
            logging.error("Erro fatal no processamento do ficheiro %s. Saltando linha.", path)

    def _prefetch_next_video(self, current: QueueItem) -> None:
        """Começa a otimizar o próximo vídeo pendente enquanto o atual é enviado."""
        try:
            start = self.items.index(current) + 1
        except ValueError:
            return
        for nxt in self.items[start:]:
            path = nxt.get("full_path")
            if path is None or nxt.get("sent", False) or not is_video(path):
                continue
            media.prefetch_video(path, media.find_numbered_thumbnail(path), self.worker.default_thumbnail)
            return

    async def _send_video(self, item: QueueItem, tag: str | None) -> bool:
        path = item["full_path"]
        thumb = media.find_numbered_thumbnail(path)
        self._prefetch_next_video(item)
        while True:
            result = await self.worker.send_video(
                self.channel_id, path, reply_to=self.reply_to, tag=tag, thumbnail=thumb
            )
            if result.ok:
                media.forget_prepared(path)
                self.svc.queue.mark_sent(self.channel_id, self.items, [item])
                self.rotate()
                return True
            if result.flood_wait is None:
                media.forget_prepared(path)
                return False

            logging.warning("FloodWait por %ss no upload.", result.flood_wait)
            await self._flush_docs()
            self.rotate()
            # Com um único worker, girar não adianta: é preciso esperar de verdade.
            await asyncio.sleep(result.flood_wait if len(self.workers) == 1 else 1)

    async def _queue_doc(self, item: QueueItem, tag: str | None) -> bool:
        path = item["full_path"]
        worker = self.worker
        try:
            handle = await media.fast_upload(worker.client, path)
        except Exception:
            logging.exception("Falha no upload do documento %s", path)
            return False

        self.docs.append(PendingDoc(file=handle, caption=build_caption(tag, path), client=worker.client, item=item))
        if len(self.docs) >= DOC_ALBUM_SIZE:
            await self._flush_docs()
            self.rotate()
        return True

    async def _flush_docs(self) -> None:
        """Envia o álbum pendente e só então marca os documentos como enviados."""
        if not self.docs:
            return
        docs, self.docs = self.docs, []
        sent = await send_grouped_docs(self.channel_id, docs, reply_to=self.reply_to)
        self.svc.queue.mark_sent(self.channel_id, self.items, [d.item for d in sent])
