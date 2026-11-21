from pathlib import Path

from app.services.channels import normalize_channel_id
from app.services.queue_store import QueueStore
from app.services.rendering import (
    build_caption,
    render_course_summary,
    render_subfolder_header,
    split_html_message,
)
from app.services.scanner import build_tag_plan, order_queue, scan_folder
from app.utils.text import column_letter, natural_key


def make_course(root: Path) -> None:
    (root / "02_Modulo_B").mkdir(parents=True)
    (root / "01_Modulo_A" / "sub").mkdir(parents=True)
    for rel in [
        "01_Modulo_A/10_aula.mp4",
        "01_Modulo_A/2_aula.mp4",
        "01_Modulo_A/2_apostila.pdf",
        "01_Modulo_A/sub/1_extra.pdf",
        "02_Modulo_B/1_intro.mp4",
        "02_Modulo_B/thumb.jpg",      # capa: deve ser ignorada
        "02_Modulo_B/diagrama.png",   # imagem comum: entra
        "solto.pdf",
    ]:
        (root / rel).write_bytes(b"x")


def test_natural_key_and_letters():
    assert sorted(["aula_10", "aula_2", "aula_1"], key=natural_key) == ["aula_1", "aula_2", "aula_10"]
    assert [column_letter(i) for i in (1, 26, 27, 28)] == ["A", "Z", "AA", "AB"]


def test_scan_is_natural_ordered_and_ignores_covers(tmp_path):
    make_course(tmp_path)
    items = scan_folder(tmp_path)
    names = [i["file_name"] for i in items]
    assert "thumb.jpg" not in names
    assert "diagrama.png" in names
    mod_a = [i["file_name"] for i in items if i["materia"] == "01_Modulo_A" and not i["subfolder"]]
    assert mod_a.index("2_aula.mp4") < mod_a.index("10_aula.mp4")  # 2 antes de 10
    solto = next(i for i in items if i["file_name"] == "solto.pdf")
    assert solto["materia"] == "GERAL" and solto["subfolder"] == ""
    sub = next(i for i in items if i["file_name"] == "1_extra.pdf")
    assert (sub["materia"], sub["subfolder"]) == ("01_Modulo_A", "sub")
    assert all(i["sent"] is False for i in items)


def test_order_and_tag_plan(tmp_path):
    make_course(tmp_path)
    items = order_queue(scan_folder(tmp_path))
    mod_a = [i["file_name"] for i in items if i["materia"] == "01_Modulo_A" and not i["subfolder"]]
    assert mod_a[:2] == ["2_aula.mp4", "10_aula.mp4"]  # vídeos antes dos docs

    _, file_tags = build_tag_plan(items)
    by_name = {Path(p).name: t for p, t in file_tags.items()}
    # o PDF herda a tag do vídeo de mesmo prefixo numérico
    assert by_name["2_apostila.pdf"] == by_name["2_aula.mp4"]
    assert by_name["2_aula.mp4"].endswith("001") and by_name["10_aula.mp4"].endswith("002")


def test_split_html_message_balances_blockquotes_and_never_loops():
    body = "<blockquote>" + "\n".join(f"linha {i}" for i in range(2000)) + "</blockquote>"
    chunks = split_html_message(body, limit=500)
    assert len(chunks) > 1 and all(len(c) <= 520 for c in chunks)
    assert all(c.count("<blockquote>") == c.count("</blockquote>") for c in chunks)
    # texto que começa com quebra de linha e sem outra: antes gerava loop infinito
    assert split_html_message("\n" + "a" * 900, limit=500)
    assert split_html_message("curto") == ["curto"]


def test_rendering_escapes_html():
    assert "&amp;" in build_caption("A001", "/x/01_Tom & Jerry.mp4")
    assert "&lt;B&gt;X" in render_subfolder_header("01_<b>x", "A", "L")  # o nome vai em maiúsculas
    assert "&amp;" in render_course_summary([{"materia": "01_A & B"}])


def test_normalize_channel_id():
    assert normalize_channel_id("123") == -100123
    assert normalize_channel_id("-100123") == -100123
    assert normalize_channel_id(" 123 ") == -100123
    assert normalize_channel_id("-5") == -5  # antes: ValueError
    assert normalize_channel_id("abc") is None


def test_queue_store_atomic_roundtrip(tmp_path):
    store = QueueStore(tmp_path)
    items = [{"full_path": "a", "materia": "m", "subfolder": "", "file_name": "a", "sent": False},
             {"full_path": "b", "materia": "m", "subfolder": "", "file_name": "b", "sent": False}]
    store.save(-100, items)
    store.mark_sent(-100, items, [items[0]])
    loaded = store.load(-100)
    assert [i["sent"] for i in loaded] == [True, False]
    assert not list(tmp_path.glob("*.tmp"))
    assert store.stamp_topic(items, "m", 7) is True and store.stamp_topic(items, "m", 7) is False


def test_scan_ignores_tooling_folders(tmp_path):
    from app.services.scanner import scan_folder

    (tmp_path / "Curso").mkdir()
    (tmp_path / "Curso" / "1_a.mp4").write_bytes(b"v")
    for junk in ("venv/lib", "node_modules/x", "Curso/__pycache__", ".git"):
        (tmp_path / junk).mkdir(parents=True)
        (tmp_path / junk / "lixo.pyc").write_bytes(b"x")
    assert [i["file_name"] for i in scan_folder(tmp_path)] == ["1_a.mp4"]
