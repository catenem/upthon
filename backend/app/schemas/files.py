from __future__ import annotations

from typing import List

from pydantic import BaseModel


class MoveFileRequest(BaseModel):
    source_path: str
    destination_folder: str


class ReorderRequest(BaseModel):
    folder_path: str
    ordered_paths: List[str]
