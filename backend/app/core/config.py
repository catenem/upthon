from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend
load_dotenv(BASE_DIR / ".env")

# --- Extensões, separadas por finalidade -------------------------------------
# Enviadas como vídeo (ffmpeg + thumbnail). Qualquer outra coisa vai como documento.
UPLOAD_VIDEO_EXTS = (".mp4", ".ts", ".avi")
# Saída temporária do ffmpeg ao lado do vídeo. Nunca é conteúdo do curso: o scanner a ignora.
TEMP_VIDEO_SUFFIX = "_ready.mp4"
# Extensões que recebem o atributo DocumentAttributeVideo no Telegram.
VIDEO_ATTRIBUTE_EXTS = (".mp4", ".mov", ".mkv", ".avi")
# Contagem na árvore de arquivos exibida no front.
TREE_VIDEO_EXTS = (
    ".mp4", ".mkv", ".ts", ".mov", ".avi", ".webm",
    ".flv", ".m4v", ".mpeg", ".mpg", ".m2ts",
)
# Contagem no dashboard.
DASHBOARD_VIDEO_EXTS = (".mp4", ".ts", ".mov")

IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
IGNORED_COVER_NAMES = frozenset({"thumb", "cover", "summary", "thumbnail", "capa"})
THUMBNAIL_NAMES = ("thumb", "cover", "thumbnail", "eef", "thumbnail_video")

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
# Pastas de código/ferramentas que nunca são conteúdo de curso (evita subir um venv por engano)
IGNORED_DIRS = {"venv", ".venv", "node_modules", "__pycache__", ".git", ".idea", ".vscode"}
DOC_ALBUM_SIZE = 10          # documentos por álbum no Telegram
TELEGRAM_TEXT_LIMIT = 4000   # limite real é 4096; folga para as tags de fechamento


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    assets_dir: Path
    db_path: Path
    cors_origins: tuple[str, ...]
    default_thumbnail: Path | None
    separator_sticker_set: str
    host: str
    port: int
    frontend_dir: Path | None = None   # build do React (index.html); None = não servir o front


def _env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    return Path(raw).expanduser() if raw else default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    assets = _env_path("UPTHON_ASSETS_DIR", BASE_DIR / "assets")
    origins = os.getenv("UPTHON_CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        base_dir=BASE_DIR,
        assets_dir=assets,
        db_path=_env_path("UPTHON_DB_PATH", BASE_DIR / "db.db"),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        default_thumbnail=_env_path("UPTHON_DEFAULT_THUMBNAIL", assets / "default_thumb.jpg"),
        separator_sticker_set=os.getenv("UPTHON_SEPARATOR_STICKER_SET", "vizualseparator"),
        host=os.getenv("UPTHON_HOST", "127.0.0.1"),
        port=int(os.getenv("UPTHON_PORT", "5000")),
        frontend_dir=_env_path("UPTHON_FRONTEND_DIR", BASE_DIR.parent / "frontend" / "build"),
    )
