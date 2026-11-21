import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        base_dir=tmp_path, assets_dir=tmp_path / "assets", db_path=tmp_path / "db.db",
        cors_origins=("http://localhost:3000",), default_thumbnail=None,
        separator_sticker_set="x", host="127.0.0.1", port=5000,
    )
    with TestClient(create_app(settings), raise_server_exceptions=False) as c:
        c.tmp = tmp_path
        yield c


def test_auth_status_unauthenticated(client):
    assert client.get("/api/auth/status").json() == {"authorized": False}


def test_user_me_requires_login(client):
    r = client.get("/api/user/me")
    assert r.status_code == 401 and r.json() == {"detail": "Não conectado"}


def test_login_rejects_bad_api_id(client):
    r = client.post("/api/auth/login", json={"api_id": "abc", "api_hash": "h", "phone": "+55"})
    assert r.status_code == 400
    r = client.post("/api/auth/login", json={"api_id": "99999999999", "api_hash": "h", "phone": "+55"})
    assert r.status_code == 400 and "inválido" in r.json()["detail"]


def test_verify_without_login_is_404(client):
    r = client.post("/api/auth/verify", json={"phone": "+55", "code": "1"})
    assert r.status_code == 404


def test_start_upload_without_workers_is_400(client):
    r = client.post("/api/start-upload", json={"channelName": "c", "typeChannel": "channel", "folderPath": "/x"})
    assert r.status_code == 400 and "worker" in r.json()["detail"]


def test_list_reorder_move(client):
    root = client.tmp / "course"
    (root / "b").mkdir(parents=True)
    (root / "a.mp4").write_bytes(b"1")
    (root / "b" / "x.pdf").write_bytes(b"1")

    tree = client.get("/api/list-files", params={"path": str(root)}).json()
    assert tree["subfolders"] == 1
    kids = {c["real_name"]: c for c in tree["children"]}
    assert kids["a.mp4"]["type"] == "file" and kids["b"]["pdf_count"] == 1

    assert client.get("/api/list-files", params={"path": str(root / "nope")}).status_code == 404

    r = client.post("/api/reorder-files", json={"folder_path": str(root), "ordered_paths": [str(root / "a.mp4")]})
    assert r.status_code == 200 and (root / "01_a.mp4").exists()

    r = client.post("/api/move-file", json={"source_path": str(root / "01_a.mp4"), "destination_folder": str(root / "b")})
    assert r.json()["status"] == "success" and (root / "b" / "01_a.mp4").exists()


def test_dashboard_and_pending(client):
    assets = client.tmp / "assets"
    (assets / "upload_-100111.json").write_text(json.dumps([
        {"file_name": "a.mp4", "sent": True}, {"file_name": "b.pdf", "sent": False},
        {"file_name": "c.mov", "sent": False}]), encoding="utf-8")
    (assets / "upload_-100222.json").write_text(json.dumps([{"file_name": "z.pdf", "sent": True}]), encoding="utf-8")
    (assets / "upload_-100333.json").write_text("{corrompido", encoding="utf-8")   # não pode derrubar a rota

    assert client.get("/api/pending-uploads").json() == {"pending_channels": ["-100111"]}

    data = client.get("/api/dashboard/stats").json()
    assert data["total_channels"] == 2
    assert data["overall_stats"] == {"total_items": 4, "total_sent": 2, "total_pending": 2, "progress_percentage": 50.0}
    ch = next(c for c in data["channels"] if c["channel_id"] == "-100111")
    assert (ch["mp4_sent"], ch["mp4_pending"], ch["pdf_pending"], ch["progress_percentage"]) == (1, 1, 1, 33.33)


def test_bots_list_empty_and_empty_token(client):
    assert client.get("/api/bots/infos").json() == []
    r = client.post("/api/bots/add", json={"token": "   "})
    assert r.status_code == 400


def test_db_migration_adds_avatar_column(tmp_path):
    import sqlite3
    from app.db.repository import Repository
    db = tmp_path / "old.db"
    with sqlite3.connect(db) as conn:  # esquema antigo, sem avatar_url
        conn.execute("CREATE TABLE bots (id INTEGER PRIMARY KEY, bot_token TEXT UNIQUE, bot_username TEXT, is_active INTEGER DEFAULT 1)")
    repo = Repository(db)
    repo.init_schema()
    repo.upsert_bot("tok", "bot1", "")
    assert repo.list_active_bots()[0]["avatar_url"] is None


def test_dashboard_items_page_and_light_stats(client):
    assets = client.tmp / "assets"
    (assets / "upload_-100111.json").write_text(json.dumps(
        [{"file_name": f"{i}.mp4", "sent": i % 2 == 0} for i in range(5)]), encoding="utf-8")
    (assets / "upload_-100222.json").write_text(json.dumps([{"file_name": "z.pdf", "sent": True}]), encoding="utf-8")

    light = client.get("/api/dashboard/stats?include_items=false").json()
    assert all("items" not in c for c in light["channels"]) and light["overall_stats"]["total_items"] == 6

    page = client.get("/api/dashboard/items?channel_id=-100111&offset=1&limit=2").json()
    assert page["total"] == 5 and [i["file_name"] for i in page["items"]] == ["1.mp4", "2.mp4"]
    assert page["items"][0]["channel_id"] == "-100111"
    assert client.get("/api/dashboard/items").json()["total"] == 6
    assert client.get("/api/dashboard/items?limit=0").status_code == 422


def test_frontend_served_with_spa_fallback(tmp_path):
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from app.core.config import get_settings
    from app.main import create_app

    build = tmp_path / "build"
    (build / "static").mkdir(parents=True)
    (build / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
    (build / "static" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("nao pode sair", encoding="utf-8")

    base = get_settings()
    settings = replace(base, frontend_dir=build, db_path=tmp_path / "t.db", assets_dir=tmp_path / "assets")
    with TestClient(create_app(settings)) as c:
        assert c.get("/").text == "<html>SPA</html>"
        assert c.get("/dashboard").text == "<html>SPA</html>"          # rota do react-router
        assert c.get("/static/app.js").text == "console.log(1)"
        assert "nao pode sair" not in c.get("/../segredo.txt").text
        assert "nao pode sair" not in c.get("/%2e%2e/segredo.txt").text
        assert c.get("/api/rota-que-nao-existe").status_code == 404
        assert c.get("/api/pending-uploads").status_code == 200        # a API continua funcionando
