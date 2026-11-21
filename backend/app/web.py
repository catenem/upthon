"""Serve o build do React (``npm run build``) pelo próprio FastAPI: um processo só, sem Node."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_frontend(app: FastAPI, build_dir: Path | None) -> bool:
    """Registra a rota que entrega o front. Devolve False (e não faz nada) se não há build."""
    if build_dir is None or not (build_dir / "index.html").is_file():
        logging.info("Build do front não encontrado em %s; só a API está ativa.", build_dir)
        return False

    root = build_dir.resolve()
    index = root / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Rota não encontrada.")
        candidate = (root / path).resolve()
        # arquivo do build (js, css, svg...) se existir e estiver dentro da pasta; senão o SPA assume
        if path and candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)

    logging.info("Front servido a partir de %s", root)
    return True
