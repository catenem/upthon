from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ContainerDep

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(c: ContainerDep, include_items: bool = True):
    """``include_items=false`` devolve só os totais (leve); a lista vem de ``/items``."""
    return c.dashboard.stats(include_items)


@router.get("/items")
def items(
    c: ContainerDep,
    channel_id: str = "ALL",
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    return c.dashboard.items_page(channel_id, offset, limit)
