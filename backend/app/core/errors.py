"""Exceções de domínio. Os services lançam estas; um handler global converte em HTTP.

O corpo da resposta continua ``{"detail": ...}``, igual ao ``HTTPException`` que o
front já conhece.
"""
from __future__ import annotations

from typing import Any


class UpthonError(Exception):
    status_code = 500
    default_detail: Any = "Erro interno."

    def __init__(self, detail: Any = None) -> None:
        self.detail = detail if detail is not None else self.default_detail
        super().__init__(str(self.detail))


class BadRequest(UpthonError):
    status_code = 400


class Unauthorized(UpthonError):
    status_code = 401


class NotFound(UpthonError):
    status_code = 404


class Conflict(UpthonError):
    status_code = 409


class RateLimited(UpthonError):
    status_code = 429


class InternalError(UpthonError):
    status_code = 500


class ServiceUnavailable(UpthonError):
    status_code = 503
