from __future__ import annotations

from fastapi import APIRouter

from app.schemas.files import MoveFileRequest, ReorderRequest
from app.services import file_browser
from app.services.folder_picker import pick_folder

router = APIRouter(prefix="/api", tags=["files"])

# Rotas síncronas (def): o FastAPI as executa em thread pool, sem bloquear o event loop.


@router.post("/move-file")
def move_file(request: MoveFileRequest):
    return {"status": "success", "new_path": file_browser.move_file(request.source_path, request.destination_folder)}


@router.get("/list-files")
def list_files(path: str):
    return file_browser.list_directory(path)


@router.post("/reorder-files")
def reorder_files(request: ReorderRequest):
    file_browser.reorder_files(request.ordered_paths)
    return {"status": "success"}


@router.get("/browse-folder")
def browse_folder():
    return {"path": pick_folder()}
