"""CLI: navegação por índice, tipo do canal, pendentes e retomada (sem Telegram)."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.cli.app import CliApp
from app.cli.fs import list_subdirs, parent_within, resolve_index
from app.cli.pending import infer_root, list_pending
from app.cli.settings_store import CliConfig
from app.services.queue_store import QueueStore


class ScriptedConsole:
    def __init__(self, answers):
        self.answers = list(answers)
        self.out: list[str] = []

    def say(self, text=""):
        self.out.append(text)

    async def ask(self, prompt):
        self.out.append(prompt)
        return self.answers.pop(0) if self.answers else "q"

    async def ask_secret(self, prompt):
        return await self.ask(prompt)

    async def confirm(self, prompt, default=False):
        a = (await self.ask(prompt)).lower()
        return default if not a else a in ("s", "y")

    @property
    def text(self):
        return "\n".join(self.out)


class FakeUploads:
    def __init__(self):
        self.calls = []

    async def ensure_workers(self):
        return True

    async def upload(self, folder, channel_id, is_topics):
        self.calls.append((folder, channel_id, is_topics))


class FakeChannels:
    def __init__(self):
        self.created = []

    async def create_channel(self, name, *, is_topic=False):
        self.created.append((name, is_topic))
        return 4242


def make_container(tmp_path):
    return SimpleNamespace(
        queue=QueueStore(tmp_path / "assets"), uploads=FakeUploads(), channels=FakeChannels(),
        is_authorized=True, repo=SimpleNamespace(get_credentials=lambda: {}),
    )


@pytest.fixture
def courses(tmp_path):
    root = tmp_path / "cursos"
    (root / "10_Python" / "01_Intro").mkdir(parents=True)
    (root / "10_Python" / "01_Intro" / "01_a.mp4").write_bytes(b"x")
    (root / "10_Python" / "01_Intro" / "02_b.pdf").write_bytes(b"x")
    (root / "2_React").mkdir()
    (root / "2_React" / "01_x.mp4").write_bytes(b"x")
    (root / "vazio").mkdir()
    (root / ".oculta").mkdir()
    return root


def test_list_subdirs_natural_order_counts_and_hidden(courses):
    entries = list_subdirs(courses)
    assert [e.name for e in entries] == ["2_React", "10_Python", "vazio"]   # natural, sem oculta
    assert [(e.index, e.videos, e.docs) for e in entries] == [(1, 1, 0), (2, 1, 1), (3, 0, 0)]
    assert resolve_index(entries, "2").name == "10_Python"
    assert resolve_index(entries, "9") is None and resolve_index(entries, "x") is None


def test_parent_within_stops_at_root(courses):
    assert parent_within(courses, courses) is None
    assert parent_within(courses / "10_Python", courses) == courses


async def test_index_asks_channel_type_then_uploads(tmp_path, courses):
    c = make_container(tmp_path)
    # ordem das perguntas: índice -> tipo (1 = canal privado) -> nome (Enter = padrão) -> confirmação
    io = ScriptedConsole(["2", "1", "", "s", "q"])
    await CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses).run()
    assert c.channels.created == [("Python", False)]
    assert c.uploads.calls == [(str(courses / "10_Python"), 4242, False)]


async def test_supergroup_type_and_custom_name(tmp_path, courses):
    c = make_container(tmp_path)
    io = ScriptedConsole(["1", "2", "Meu React", "s", "q"])
    await CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses).run()
    assert c.channels.created == [("Meu React", True)]
    assert c.uploads.calls[0][2] is True


async def test_cancel_and_invalid_inputs_do_not_upload(tmp_path, courses):
    c = make_container(tmp_path)
    io = ScriptedConsole(["99", "abc", "1", "0", "1", "1", "", "n", "q"])
    await CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses).run()
    assert c.uploads.calls == [] and c.channels.created == []
    assert "Comando não reconhecido" in io.text


async def test_open_back_and_root_limit(tmp_path, courses):
    c = make_container(tmp_path)
    io = ScriptedConsole(["a 2", "..", "..", "q"])
    app = CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses)
    await app.run()
    assert app.current == courses
    assert "Você já está na pasta raiz." in io.text
    assert "01_Intro" in io.text            # listou a subpasta ao abrir a pasta 2


async def test_set_root_persists(tmp_path, courses):
    c = make_container(tmp_path)
    cfg = CliConfig(tmp_path / "cfg.json")
    await CliApp(c, ScriptedConsole(["d", str(courses), "q"]), cfg, start=Path(tmp_path)).run()
    assert cfg.load_root() == courses.resolve()


def _queue(tmp_path, channel, items):
    d = tmp_path / "assets"
    d.mkdir(exist_ok=True)
    (d / f"upload_{channel}.json").write_text(json.dumps(items), encoding="utf-8")


def test_infer_root_and_pending_listing(tmp_path):
    base = "/cursos/Python"
    _queue(tmp_path, "-1001", [
        {"full_path": f"{base}/10_Mod/01_Aula/a.mp4", "materia": "10_Mod", "subfolder": "01_Aula", "file_name": "a.mp4", "sent": True, "topic_id": 7},
        {"full_path": f"{base}/10_Mod/b.pdf", "materia": "10_Mod", "subfolder": "", "file_name": "b.pdf", "sent": False},
    ])
    _queue(tmp_path, "-1002", [{"full_path": f"{base}/solto.mp4", "materia": "GERAL", "subfolder": "", "file_name": "solto.mp4", "sent": False}])
    _queue(tmp_path, "-1003", [{"full_path": "/x/a.mp4", "materia": "M", "subfolder": "", "file_name": "a.mp4", "sent": True}])  # completo
    (tmp_path / "assets" / "upload_-1004.json").write_text("{quebrado", encoding="utf-8")

    pend = {p.channel_id: p for p in list_pending(QueueStore(tmp_path / "assets"))}
    assert set(pend) == {"-1001", "-1002"}
    assert pend["-1001"].root == Path(base) and pend["-1001"].is_topics is True
    assert (pend["-1001"].sent, pend["-1001"].total, pend["-1001"].remaining) == (1, 2, 1)
    assert pend["-1002"].root == Path(base) and pend["-1002"].is_topics is None
    assert infer_root([]) is None


async def test_resume_known_topics_and_unknown_asks_type(tmp_path, courses):
    base = str(courses / "10_Python")
    _queue(tmp_path, "-1001", [
        {"full_path": f"{base}/01_Intro/01_a.mp4", "materia": "01_Intro", "subfolder": "", "file_name": "01_a.mp4", "sent": False, "topic_id": 3}])
    _queue(tmp_path, "-1002", [
        {"full_path": f"{base}/01_Intro/02_b.pdf", "materia": "01_Intro", "subfolder": "", "file_name": "02_b.pdf", "sent": False}])
    c = make_container(tmp_path)
    # 1) retoma canal -1001 (tópicos já conhecido: não pergunta o tipo) | 2) retoma -1002 (pergunta tipo -> privado)
    io = ScriptedConsole(["p", "1", "", "p", "2", "1", "", "q"])
    await CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses).run()
    assert c.uploads.calls == [(base, "-1001", True), (base, "-1002", False)]
    assert c.channels.created == []        # retomar nunca cria canal novo


async def test_no_pending_message(tmp_path, courses):
    c = make_container(tmp_path)
    io = ScriptedConsole(["p", "q"])
    await CliApp(c, io, CliConfig(tmp_path / "cfg.json"), start=courses).run()
    assert "Nenhum upload pendente" in io.text
