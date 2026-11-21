from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks

from app.api.deps import ContainerDep
from app.core.errors import BadRequest, Conflict
from app.schemas.uploads import ResumePayload, UploadPayload

router = APIRouter(prefix="/api", tags=["uploads"])

_NO_WORKERS = "Nenhum worker (Admin ou Bot) disponível para upload."


@router.get("/pending-uploads")
def pending_uploads(c: ContainerDep):
    return {"pending_channels": c.dashboard.pending_channels()}


@router.post("/start-upload")
async def start_upload(payload: UploadPayload, background_tasks: BackgroundTasks, c: ContainerDep):
    if not await c.uploads.ensure_workers():
        raise BadRequest(_NO_WORKERS)

    is_topics = "topic" in payload.typeChannel.lower()
    logging.info("Criando canal '%s'...", payload.channelName)
    channel_id = await c.channels.create_channel(payload.channelName, is_topic=is_topics)

    background_tasks.add_task(c.uploads.run_job, payload.folderPath, channel_id, is_topics)
    return {"message": "Upload iniciado", "channel_id": channel_id}


@router.post("/resume-upload")
async def resume_upload(payload: ResumePayload, background_tasks: BackgroundTasks, c: ContainerDep):
    if not await c.uploads.ensure_workers():
        raise BadRequest(_NO_WORKERS)
    if c.uploads.is_running(payload.channel_id):
        raise Conflict("Já existe um upload em andamento para este canal.")

    background_tasks.add_task(c.uploads.run_job, payload.folderPath, payload.channel_id, payload.is_topics)
    return {
        "message": f"Retomada de upload para o canal {payload.channel_id} iniciada em segundo plano!",
        "channel_id": payload.channel_id,
    }
