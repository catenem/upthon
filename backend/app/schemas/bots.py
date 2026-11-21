from __future__ import annotations

from pydantic import BaseModel


class BotSchema(BaseModel):
    token: str
