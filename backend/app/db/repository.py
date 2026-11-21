"""Acesso ao SQLite (antes misturado com o cliente Telethon em ``TelegramModel``)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class Repository:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # ``with sqlite3.connect()`` só faz commit e NÃO fecha a conexão; aqui fecha.
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Cria tabelas e aplica a migração de ``avatar_url`` (um único lugar)."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_id INTEGER,
                    api_hash TEXT,
                    phone TEXT UNIQUE,
                    session_str TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_token TEXT UNIQUE NOT NULL,
                    bot_username TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    avatar_url TEXT
                )
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(bots)")}
            if "avatar_url" not in columns:
                conn.execute("ALTER TABLE bots ADD COLUMN avatar_url TEXT")

    # --- credenciais do admin -------------------------------------------------
    def save_credentials(self, api_id: int, api_hash: str, phone: str) -> None:
        """Mantém apenas um admin: apaga o anterior."""
        with self._connect() as conn:
            conn.execute("DELETE FROM settings")
            conn.execute(
                "INSERT INTO settings (api_id, api_hash, phone) VALUES (?, ?, ?)",
                (int(api_id), api_hash, phone),
            )

    def update_session_string(self, phone: str, session_str: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE settings SET session_str = ? WHERE phone = ?", (session_str, phone))

    def get_credentials(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()
            return dict(row) if row else None

    # --- bots -----------------------------------------------------------------
    def list_active_bots(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM bots WHERE is_active = 1").fetchall()
        bots = [dict(r) for r in rows]
        for bot in bots:
            bot["avatar_url"] = bot.get("avatar_url") or None
        return bots

    def set_avatar(self, bot_id: int, avatar_url: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE bots SET avatar_url = ? WHERE id = ?", (avatar_url, bot_id))

    def upsert_bot(self, token: str, username: str, avatar_url: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bots (bot_token, bot_username, is_active, avatar_url)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(bot_token) DO UPDATE SET
                    is_active = 1,
                    bot_username = excluded.bot_username,
                    avatar_url = excluded.avatar_url
                """,
                (token, username, avatar_url),
            )
