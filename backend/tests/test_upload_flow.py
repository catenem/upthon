"""Fluxo completo do upload com um cliente Telegram falso (sem rede, sem ffmpeg)."""
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services import media
from app.services.channels import ChannelService
from app.services.queue_store import QueueStore
from app.services.upload_service import UploadService
from app.services.workers import TelegramWorker


class FakeClient:
    def __init__(self, fail_files=False):
        self.sent = []            # (kind, payload) na ordem em que saíram
        self.fail_files = fail_files

    async def get_entity(self, _):
        return SimpleNamespace()

    async def upload_file(self, path):
        return f"handle:{path}"

    async def send_message(self, chat, text, **kw):
        self.sent.append(("text", text))

    async def send_file(self, chat, file=None, **kw):
        if isinstance(file, str) and file.startswith("handle:") or isinstance(file, list):
            if self.fail_files:
                raise RuntimeError("boom")
            self.sent.append(("docs", file if isinstance(file, list) else [file]))
        else:
            self.sent.append(("file", file))

    async def __call__(self, request):
        return SimpleNamespace(documents=["sticker0", "sticker1"])


class FakePool:
    def __init__(self, worker):
        self.workers = [worker]
        self.admin = worker

    def active(self, *, only_bots=False):
        return list(self.workers)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        base_dir=tmp_path, assets_dir=tmp_path / "assets", db_path=tmp_path / "db.db",
        cors_origins=(), default_thumbnail=None, separator_sticker_set="x", host="h", port=1,
    )


def build_service(tmp_path, settings, client, monkeypatch):
    async def fake_prepare(video_path, numbered_thumb, default_thumb):
        return media.PreparedVideo(path=video_path, thumb=None, duration=5)

    monkeypatch.setattr(media, "prepare_video", fake_prepare)
    pool = FakePool(TelegramWorker(client, "admin"))
    return UploadService(pool, ChannelService(pool), QueueStore(settings.assets_dir), settings)


def make_course(root):
    (root / "01_Mod").mkdir(parents=True)
    (root / "01_Mod" / "1_aula.mp4").write_bytes(b"v")
    (root / "01_Mod" / "1_apostila.pdf").write_bytes(b"p")
    (root / "01_Mod" / "2_extra.pdf").write_bytes(b"p")


async def test_full_upload_then_resume_sends_nothing_twice(tmp_path, settings, monkeypatch):
    course = tmp_path / "course"
    make_course(course)
    client = FakeClient()
    svc = build_service(tmp_path, settings, client, monkeypatch)

    await svc.upload(str(course), "999", is_topics=False)

    videos = [p for k, p in client.sent if k == "file" and str(p).endswith(".mp4")]
    assert len(videos) == 1
    # vídeo é enviado antes do álbum de documentos
    first_video = next(i for i, (k, _) in enumerate(client.sent) if k == "file" and str(_).endswith("1_aula.mp4"))
    first_docs = next(i for i, (k, _) in enumerate(client.sent) if k == "docs")
    assert first_video < first_docs
    docs = [p for k, p in client.sent if k == "docs"]
    assert sum(len(p) for p in docs) == 2

    items = svc.queue.load(-100999)
    assert all(i["sent"] for i in items)

    before = len(client.sent)
    await svc.upload(str(course), "999", is_topics=False)   # retomada: tudo já enviado
    resent = client.sent[before:]
    assert not [1 for k, p in resent if k == "docs" or (k == "file" and str(p).endswith(".mp4"))]


async def test_docs_not_marked_sent_when_send_fails(tmp_path, settings, monkeypatch):
    """Bug antigo: documentos eram marcados como enviados ao entrar no buffer."""
    course = tmp_path / "course"
    make_course(course)
    client = FakeClient(fail_files=True)
    svc = build_service(tmp_path, settings, client, monkeypatch)

    await svc.upload(str(course), "999")

    by_name = {i["file_name"]: i["sent"] for i in svc.queue.load(-100999)}
    assert by_name["1_aula.mp4"] is True
    assert by_name["1_apostila.pdf"] is False and by_name["2_extra.pdf"] is False


async def test_concurrent_duplicate_upload_is_refused(tmp_path, settings, monkeypatch):
    course = tmp_path / "course"
    make_course(course)
    svc = build_service(tmp_path, settings, FakeClient(), monkeypatch)
    svc._running.add(-100999)
    assert svc.is_running("999")
    await svc.upload(str(course), "999")
    assert not svc.queue.exists(-100999)  # nem chegou a criar a fila


def test_prepare_video_reuses_prefetched_result(monkeypatch):
    import asyncio
    from app.services import media

    calls = []

    async def fake(path, numbered, default):
        calls.append(path)
        await asyncio.sleep(0)
        return media.PreparedVideo(path=path, thumb=None, duration=3)

    monkeypatch.setattr(media, "_prepare_video", fake)
    media._prepared.clear()

    async def scenario():
        media.prefetch_video("/x/a.mp4", None, None)
        first = await media.prepare_video("/x/a.mp4", None, None)   # reaproveita o prefetch
        again = await media.prepare_video("/x/a.mp4", None, None)   # nova tentativa: sem reencodar
        media.forget_prepared("/x/a.mp4")
        third = await media.prepare_video("/x/a.mp4", None, None)   # depois de enviado: refaz
        return first, again, third

    first, again, third = asyncio.run(scenario())
    assert first is again and third is not first
    assert len(calls) == 2


class TopicClient(FakeClient):
    """Registra o reply_to de cada envio (None = foi para o General)."""

    def __init__(self):
        super().__init__()
        self.targets = []

    async def send_message(self, chat, text, **kw):
        self.targets.append(("text", kw.get("reply_to")))
        await super().send_message(chat, text, **kw)

    async def send_file(self, chat, file=None, **kw):
        self.targets.append(("file", kw.get("reply_to")))
        await super().send_file(chat, file=file, **kw)


def make_two_materias(root):
    for name in ("A", "B"):
        (root / name).mkdir(parents=True)
        (root / name / "1_aula.mp4").write_bytes(b"v")


async def test_resume_creates_topic_for_materia_without_id(tmp_path, settings, monkeypatch):
    """Bug real: A já tinha tópico, B não; a retomada mandou B para o General."""
    course = tmp_path / "course"
    make_two_materias(course)
    client = TopicClient()
    svc = build_service(tmp_path, settings, client, monkeypatch)

    from app.services.scanner import scan_folder
    items = scan_folder(course)
    for i in items:
        if i["materia"] == "A":
            i["sent"], i["topic_id"], i["topic_name"] = True, 103, "A"
    svc.queue.save(-100999, items)

    created = []

    async def fake_topic(chat_id, name):
        created.append(name)
        return 555

    monkeypatch.setattr(svc.channels, "get_or_create_topic", fake_topic)

    await svc.upload(str(course), "999", is_topics=False)       # quem retomou esqueceu o is_topics

    assert created == ["B"]                                      # só B; A já tinha id e estava completa
    assert client.targets and all(target == 555 for _, target in client.targets)   # nada foi ao General
    saved = {i["materia"]: (i["topic_id"], i["topic_name"], i["sent"]) for i in svc.queue.load(-100999)}
    assert saved == {"A": (103, "A", True), "B": (555, "B", True)}


async def test_topic_creation_failure_stops_instead_of_using_general(tmp_path, settings, monkeypatch):
    course = tmp_path / "course"
    make_two_materias(course)
    client = TopicClient()
    svc = build_service(tmp_path, settings, client, monkeypatch)

    async def broken(chat_id, name):
        return None

    monkeypatch.setattr(svc.channels, "get_or_create_topic", broken)

    with pytest.raises(Exception, match="tópico"):
        await svc._upload(str(course), -100999, svc.pool.workers, True)

    assert client.targets == []                                   # nada saiu
    assert not any(i["sent"] for i in svc.queue.load(-100999))     # tudo continua pendente
