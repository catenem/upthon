"""O token do bot e a string de sessão nunca podem sair pela API."""
import asyncio
import base64

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.telegram_session import VerifyResult

TOKEN = "123456789:AAH-segredo-do-bot"
JPEG = b"\xff\xd8\xff-fake-jpeg-bytes"


def telegram_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/getMe"):
        return httpx.Response(200, json={"ok": True, "result": {"id": 123456789, "username": "meubot"}})
    if path.endswith("/getUserProfilePhotos"):
        return httpx.Response(200, json={"ok": True, "result": {"total_count": 1, "photos": [[{"file_id": "F"}]]}})
    if path.endswith("/getFile"):
        return httpx.Response(200, json={"ok": True, "result": {"file_path": "photos/file_1.jpg"}})
    if "/file/bot" in path:
        return httpx.Response(200, content=JPEG)
    return httpx.Response(404)


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        base_dir=tmp_path, assets_dir=tmp_path / "assets", db_path=tmp_path / "db.db",
        cors_origins=(), default_thumbnail=None, separator_sticker_set="x", host="h", port=1,
    )
    with TestClient(create_app(settings), raise_server_exceptions=False) as c:
        c.container = c.app.state.container
        c.container.bots._transport = httpx.MockTransport(telegram_handler)
        yield c


def test_add_bot_stores_avatar_as_data_uri_and_listing_hides_token(client):
    r = client.post("/api/bots/add", json={"token": f"  {TOKEN}  "})
    assert r.status_code == 200 and "@meubot" in r.json()["message"]

    r = client.get("/api/bots/infos")
    body = r.text
    assert "AAH-segredo" not in body and "bot_token" not in body

    (bot,) = r.json()
    assert bot["bot_username"] == "meubot"
    assert bot["token_preview"] == "123456789:…"
    prefix = "data:image/jpeg;base64,"
    assert bot["avatar_url"].startswith(prefix)
    assert base64.b64decode(bot["avatar_url"][len(prefix):]) == JPEG
    assert set(bot) == {"id", "bot_username", "is_active", "avatar_url", "token_preview"}

    # o token continua disponível para uso interno (workers)
    assert client.container.repo.list_active_bots()[0]["bot_token"] == TOKEN


def test_invalid_token_is_rejected(client):
    client.container.bots._transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json={"ok": False})
    )
    r = client.post("/api/bots/add", json={"token": "x:y"})
    assert r.status_code == 400 and "inválido" in r.json()["detail"]


def test_avatar_failure_does_not_block_adding_bot(client):
    def handler(request):
        if request.url.path.endswith("/getMe"):
            return telegram_handler(request)
        raise httpx.ConnectError("sem rede")

    client.container.bots._transport = httpx.MockTransport(handler)
    assert client.post("/api/bots/add", json={"token": TOKEN}).status_code == 200
    assert client.get("/api/bots/infos").json()[0]["avatar_url"] is None


def test_legacy_avatar_url_is_hidden_then_migrated(client):
    legacy = f"https://api.telegram.org/file/bot{TOKEN}/photos/old.jpg"
    client.container.repo.upsert_bot(TOKEN, "velho", legacy)

    r = client.get("/api/bots/infos")
    assert "AAH-segredo" not in r.text and r.json()[0]["avatar_url"] is None  # escondido

    migrated = asyncio.run(client.container.bots.refresh_legacy_avatars())
    assert migrated == 1
    assert client.get("/api/bots/infos").json()[0]["avatar_url"].startswith("data:image/jpeg;base64,")
    assert asyncio.run(client.container.bots.refresh_legacy_avatars()) == 0  # idempotente


def test_migration_keeps_legacy_row_when_network_is_down(client):
    legacy = f"https://api.telegram.org/file/bot{TOKEN}/photos/old.jpg"
    client.container.repo.upsert_bot(TOKEN, "velho", legacy)

    def down(request):
        raise httpx.ConnectError("sem rede")

    client.container.bots._transport = httpx.MockTransport(down)
    assert asyncio.run(client.container.bots.refresh_legacy_avatars()) == 0
    # continua marcado como antigo (será tentado no próximo startup), não vira ""
    assert client.container.repo.list_active_bots()[0]["avatar_url"] == legacy


def test_verify_does_not_return_session_string(client):
    async def fake_verify(phone, code, password):
        return VerifyResult(needs_password=False, session="SESSAO-SECRETA")

    async def fake_setup():
        return True

    client.container.session.verify_code = fake_verify
    client.container.pool.setup = fake_setup
    r = client.post("/api/auth/verify", json={"phone": "+55", "code": "1"})
    assert r.status_code == 200
    assert r.json() == {"status": "success", "mensagem": "Autenticado com sucesso! Redirecionando..."}
    assert "SESSAO-SECRETA" not in r.text
