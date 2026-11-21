from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LoginSchema(BaseModel):
    api_id: str
    api_hash: str
    phone: str


class VerifySchema(BaseModel):
    phone: str
    code: str
    password: Optional[str] = None
