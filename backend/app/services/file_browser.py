"""Navegação e organização de arquivos locais (árvore, mover, reordenar)."""
from __future__ import annotations

import logging
import os
import re
import shutil

from app.core.config import TREE_VIDEO_EXTS
from app.core.errors import NotFound


def _file_node(name: str, path: str) -> dict:
    lower = name.lower()
    is_mp4 = lower.endswith(".mp4")
    is_vid = lower.endswith(TREE_VIDEO_EXTS)
    is_pdf = lower.endswith(".pdf")
    return {
        "name": name,
        "real_name": name,
        "path": path.replace("\\", "/"),
        "type": "file",
        "mp4_count": int(is_mp4),
        "video_count": int(is_vid),
        "pdf_count": int(is_pdf),
        "children": [],
    }


def build_tree(path: str, is_root_child: bool = False) -> dict:
    """Árvore de diretórios com contagem de vídeos/PDFs.

    O contrato JSON foi mantido idêntico ao anterior, inclusive as chaves ``_internal_*``
    (usadas na agregação recursiva) e o fato de ``mp4_count`` espelhar ``video_count``
    nos filhos diretos da raiz.
    """
    name = os.path.basename(path) or path
    node = {
        "name": re.sub(r"^\d+_(.*)", r"\1", name),
        "real_name": name,
        "path": path.replace("\\", "/"),
        "type": "file",
        "mp4_count": 0,
        "video_count": 0,
        "pdf_count": 0,
        "children": [],
    }
    if not os.path.isdir(path):
        return node

    node["type"] = "directory"
    mp4 = video = pdf = 0
    try:
        # scandir: o tipo vem junto da listagem, sem um stat extra por arquivo
        with os.scandir(path) as it:
            entries = list(it)
        for entry in entries:
            item, full = entry.name, entry.path
            if entry.is_file():
                child = _file_node(item, full)
                node["children"].append(child)
                mp4 += child["mp4_count"]
                video += child["video_count"]
                pdf += child["pdf_count"]
            else:
                child = build_tree(full)
                node["children"].append(child)
                mp4 += child.get("_internal_mp4", 0)
                video += child.get("_internal_video", 0)
                pdf += child.get("_internal_pdf", 0)

        if is_root_child:
            node["mp4_count"] = video
            node["video_count"] = video
            node["pdf_count"] = pdf
        node["_internal_mp4"] = mp4
        node["_internal_video"] = video
        node["_internal_pdf"] = pdf
    except PermissionError:
        pass
    return node


def list_directory(path: str) -> dict:
    if not os.path.exists(path):
        raise NotFound("Caminho não encontrado.")
    with os.scandir(path) as it:
        entries = list(it)
    return {
        "name": os.path.basename(path) or path,
        "path": path.replace("\\", "/"),
        "type": "directory",
        "subfolders": sum(1 for e in entries if e.is_dir()),
        "children": [build_tree(e.path, is_root_child=True) for e in entries],
    }


def move_file(source_path: str, destination_folder: str) -> str:
    dest_dir = destination_folder if os.path.isdir(destination_folder) else os.path.dirname(destination_folder)
    new_path = os.path.join(dest_dir, os.path.basename(source_path))
    if source_path != new_path:
        shutil.move(source_path, new_path)
    return new_path


def reorder_files(ordered_paths: list[str]) -> None:
    """Renomeia para '01_nome', '02_nome'... em duas fases para evitar colisões."""
    pending: list[tuple[str, str]] = []
    for index, old_path in enumerate(ordered_paths):
        if not os.path.exists(old_path):
            continue
        folder = os.path.dirname(old_path)
        clean_name = re.sub(r"^\d+_", "", os.path.basename(old_path))
        final_path = os.path.join(folder, f"{index + 1:02d}_{clean_name}").replace("\\", "/")
        temp_path = os.path.join(folder, f"temp_{index}_{clean_name}").replace("\\", "/")
        os.rename(old_path, temp_path)
        pending.append((temp_path, final_path))

    for temp_path, final_path in pending:
        os.rename(temp_path, final_path)
    logging.info("Reordenação concluída com sucesso.")
