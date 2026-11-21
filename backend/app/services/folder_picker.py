"""Seletor nativo de pasta (tkinter). Importado sob demanda: não quebra Docker/headless."""
from __future__ import annotations

from app.core.errors import ServiceUnavailable


def pick_folder() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise ServiceUnavailable("tkinter não está disponível neste ambiente.") from exc

    root = tk.Tk()
    try:
        root.withdraw()
        root.attributes("-topmost", True)
        return filedialog.askdirectory() or ""
    finally:
        root.destroy()
