from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ContainerDep
from app.schemas.bots import BotSchema

router = APIRouter(prefix="/api/bots", tags=["bots"])


@router.post("/add")
async def add_bot(payload: BotSchema, c: ContainerDep):
    username = await c.bots.add_bot(payload.token)
    return {"success": True, "message": f"Bot @{username} adicionado com sucesso!"}


@router.get("/infos")
async def bots_info(c: ContainerDep):
    return c.bots.list_bots()
