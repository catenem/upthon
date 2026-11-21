from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class UploadPayload(BaseModel):
    channelName: str
    typeChannel: str
    folderPath: str
    folderName: Optional[str] = None


class ResumePayload(BaseModel):
    channel_id: str
    folderPath: str
    is_topics: bool = False
