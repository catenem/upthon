"""Mídia: thumbnails, otimização com ffmpeg e upload paralelo de partes."""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from telethon import errors, types
from telethon.tl import functions

from app.core.config import TEMP_VIDEO_SUFFIX, THUMBNAIL_NAMES, VIDEO_HEIGHT, VIDEO_WIDTH
from app.utils.paths import clean_path, to_long_path

_THUMB_EXTS = (".jpg", ".jpeg", ".png", ".webp")

# "veryfast" é ~2-3x mais rápido que "fast" com arquivos só um pouco maiores.
# Para qualidade/tamanho máximos: UPTHON_FFMPEG_PRESET=slow (ou fast, como era antes).
FFMPEG_PRESET = os.getenv("UPTHON_FFMPEG_PRESET", "veryfast")


# --- thumbnails ---------------------------------------------------------------
def find_numbered_thumbnail(video_path: str) -> str | None:
    """'03_aula.mp4' -> '03_*thumb.jpg' na mesma pasta; senão qualquer '*thumb.jpg'."""
    path = Path(video_path)
    m = re.match(r"^(\d+)_", path.name)
    if m:
        found = sorted(path.parent.glob(f"{m.group(1)}_*thumb.jpg"))
        if found:
            return str(found[0])
    found = sorted(path.parent.glob("*thumb.jpg"))
    return str(found[0]) if found else None


def find_nearest_thumbnail(video_path: str | None, default: Path | None) -> str | None:
    """Sobe pelas pastas atrás de thumb/cover/... ou da primeira imagem; senão o padrão."""
    fallback = str(default) if default else None
    if not video_path:
        return fallback
    try:
        current = Path(clean_path(video_path)).resolve().parent
        while current.parent != current:
            for name in THUMBNAIL_NAMES:
                for ext in _THUMB_EXTS:
                    candidate = current / f"{name}{ext}"
                    if candidate.exists():
                        return str(candidate)
            images = sorted([*current.glob("*.jpg"), *current.glob("*.jpeg"), *current.glob("*.png")])
            if images:
                return str(images[0])
            if "upload" in current.name.lower() and not current.name.startswith("01_-"):
                break
            current = current.parent
        return fallback
    except Exception as exc:
        logging.error("Erro crítico ao procurar thumbnail: %s", exc)
        return fallback


def find_summary_thumbnail(folder: str | Path) -> str | None:
    found = sorted(Path(folder).glob("*.jpg"))
    return str(found[0]) if found else None


# --- vídeo --------------------------------------------------------------------
@dataclass(frozen=True)
class PreparedVideo:
    path: str
    thumb: str | None
    duration: int
    width: int = VIDEO_WIDTH
    height: int = VIDEO_HEIGHT


def _build_ffmpeg_cmd(src: Path, intro_thumb: str, out: Path, has_audio: bool) -> list[str]:
    scale = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", "1", "-i", intro_thumb, "-i", str(src)]
    if has_audio:
        cmd += ["-f", "lavfi", "-t", "1", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        graph = f"[0:v]{scale}[v0]; [1:v]{scale}[v1]; [v0][2:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]"
        cmd += ["-filter_complex", graph, "-map", "[outv]", "-map", "[outa]"]
    else:
        graph = f"[0:v]{scale}[v0]; [1:v]{scale}[v1]; [v0][v1]concat=n=2:v=1:a=0[outv]"
        cmd += ["-filter_complex", graph, "-map", "[outv]"]
    cmd += ["-c:v", "libx264", "-crf", "23", "-preset", FFMPEG_PRESET]
    if has_audio:
        cmd += ["-c:a", "aac"]
    cmd += ["-movflags", "+faststart", str(out)]
    return cmd


def _remove_converted_source(src: Path, converted: Path) -> None:
    """Gestão de armazenamento: depois de converter (ex.: .ts -> .mp4), apaga o original.

    Só apaga se o resultado existe e não está vazio, e nunca quando o original já era .mp4
    (nesse caso o próprio arquivo foi substituído pelo otimizado).
    """
    if src.suffix.lower() == ".mp4" or converted == src:
        return
    try:
        if converted.is_file() and converted.stat().st_size > 0 and src.is_file():
            src.unlink()
            logging.info("Original removido após converter: %s -> %s", src.name, converted.name)
    except OSError as exc:
        logging.warning("Não consegui apagar o original %s: %s", src, exc)


def _probe_duration(path: str) -> int:
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path], timeout=60
        )
        return max(1, int(float(json.loads(out)["format"]["duration"])))
    except Exception:
        return 1


def _converted_sibling(video_path: str) -> str | None:
    """Se o original (.ts etc.) já foi convertido e apagado, devolve o .mp4 que o substituiu."""
    src = Path(video_path)
    if src.suffix.lower() == ".mp4":
        return None
    for candidate in (src.with_name(src.stem + TEMP_VIDEO_SUFFIX), src.with_suffix(".mp4")):
        if candidate.is_file():
            return str(candidate)
    return None


def _optimize_video_sync(input_path: str, intro_thumb: str | None) -> dict | None:
    """Prepende 1s da thumbnail e reencoda em 720p. ATENÇÃO: substitui o arquivo original."""
    src = to_long_path(Path(input_path).resolve())
    if str(src).lower().endswith(TEMP_VIDEO_SUFFIX):
        return None

    duration = 1.0
    final_path: Path | None = None
    temp_output = src.with_name(src.stem + TEMP_VIDEO_SUFFIX)
    try:
        probe = json.loads(
            subprocess.check_output(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(src)]
            )
        )
        duration = float(probe["format"]["duration"])
        has_audio = any(s.get("codec_type") == "audio" for s in probe.get("streams", []))

        subprocess.run(
            _build_ffmpeg_cmd(src, str(intro_thumb), temp_output, has_audio),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        if os.name == "nt":
            time.sleep(1)  # Windows: dá tempo de liberar o handle do arquivo

        if not temp_output.exists():
            logging.error("FFmpeg falhou ao criar o ficheiro %s", temp_output)
            return None

        final_path = src.with_suffix(".mp4")
        if final_path != src and final_path.exists():
            # Já existe OUTRO .mp4 com esse nome (ex.: aula.ts e aula.mp4 na mesma pasta): não sobrescreve.
            final_path = temp_output
        else:
            try:
                os.replace(temp_output, final_path)
            except Exception:
                final_path = temp_output

        _remove_converted_source(src, final_path)

        return {
            "duration": max(1, int(duration) + 1),  # +1s da thumbnail de abertura
            "width": VIDEO_WIDTH,
            "height": VIDEO_HEIGHT,
            "final_path": str(final_path),
        }
    except Exception as exc:
        logging.error("Erro no FFmpeg: %s", exc)
        if final_path is None:
            # ffmpeg falhou no meio: não deixa um _ready.mp4 incompleto ao lado do vídeo
            try:
                temp_output.unlink(missing_ok=True)
            except OSError:
                pass
        return {
            "duration": max(1, int(duration)),
            "width": VIDEO_WIDTH,
            "height": VIDEO_HEIGHT,
            "final_path": str(final_path) if final_path else str(src),
            "thumbnail": str(intro_thumb) if intro_thumb else None,
        }


async def optimize_video(input_path: str, intro_thumb: str | None) -> dict | None:
    # ffprobe/ffmpeg bloqueavam o event loop (subprocess.run dentro de async def)
    return await asyncio.to_thread(_optimize_video_sync, input_path, intro_thumb)


# Preparos em andamento/concluídos, por caminho. Serve a dois fins: o ffmpeg do PRÓXIMO
# vídeo roda enquanto o atual sobe (prefetch_video), e uma nova tentativa do mesmo vídeo
# (FloodWait) reaproveita o resultado em vez de reencodar.
_prepared: dict[str, "asyncio.Task[PreparedVideo | None]"] = {}


def _log_task_error(task: "asyncio.Task") -> None:
    if not task.cancelled() and task.exception():
        logging.error("Preparo de vídeo falhou: %s", task.exception())


def prefetch_video(video_path: str, numbered_thumb: str | None, default_thumb: Path | None) -> None:
    key = clean_path(video_path)
    if key not in _prepared:
        task = asyncio.ensure_future(_prepare_video(video_path, numbered_thumb, default_thumb))
        task.add_done_callback(_log_task_error)
        _prepared[key] = task


def forget_prepared(video_path: str) -> None:
    _prepared.pop(clean_path(video_path), None)


async def prepare_video(
    video_path: str, numbered_thumb: str | None, default_thumb: Path | None
) -> PreparedVideo | None:
    """Otimiza o vídeo (ou reaproveita o preparo já feito/em andamento)."""
    key = clean_path(video_path) if video_path else ""
    task = _prepared.get(key)
    if task is None:
        task = asyncio.ensure_future(_prepare_video(video_path, numbered_thumb, default_thumb))
        if key:
            _prepared[key] = task
    result = await task
    if result is None:
        _prepared.pop(key, None)  # falhou: a próxima tentativa começa do zero
    return result


async def _prepare_video(
    video_path: str, numbered_thumb: str | None, default_thumb: Path | None
) -> PreparedVideo | None:
    """Otimiza o vídeo e resolve a thumbnail final. None se o arquivo não existe/falhou."""
    if not video_path:
        logging.error("Erro: video_path vazio")
        return None
    video_path = clean_path(video_path)
    intro_thumb = find_nearest_thumbnail(video_path, default_thumb)

    converted = None
    if not os.path.exists(video_path):
        # Retomada: o .ts foi convertido e apagado numa tentativa anterior. Usa o .mp4 pronto, sem reencodar
        # (reencodar de novo colocaria a abertura de 1 s duas vezes).
        converted = _converted_sibling(video_path)
        if converted is None:
            logging.error("Erro: vídeo não encontrado: %s", video_path)
            return None
        logging.info("Original já convertido; usando %s", converted)

    data = None
    if converted is None:
        try:
            data = await optimize_video(video_path, intro_thumb)
        except Exception as exc:
            logging.error("optimize_video falhou: %s", exc)
    else:
        video_path = converted
        data = {"final_path": converted, "duration": await asyncio.to_thread(_probe_duration, converted)}

    if isinstance(data, dict):
        final_path = data.get("final_path", video_path)
        duration = data.get("duration", 1)
        thumb = data.get("thumbnail")
    else:
        final_path, duration, thumb = video_path, 1, None

    if not final_path or not os.path.exists(final_path):
        logging.error("Erro: arquivo não existe após otimização: %s", final_path)
        return None

    thumb = thumb or intro_thumb
    if numbered_thumb and os.path.exists(numbered_thumb):
        thumb = numbered_thumb
    if not thumb or not os.path.exists(thumb):
        thumb = None

    return PreparedVideo(path=str(final_path), thumb=thumb, duration=int(duration))


# --- erros 500 do Telegram ---------------------------------------------------------
RETRY_DELAYS = (3, 10, 30)   # segundos entre tentativas (alterado nos testes)


async def with_server_retry(call, what: str):
    """Repete a chamada em erros 500 do Telegram (ex.: STORAGE_CHOOSE_VOLUME_*), que são passageiros."""
    for attempt, delay in enumerate((*RETRY_DELAYS, None)):
        try:
            return await call()
        except errors.ServerError as exc:
            if delay is None:
                raise
            logging.warning("Telegram com erro interno (%s) em %s; nova tentativa em %ss.", exc, what, delay)
            await asyncio.sleep(delay)


# --- upload paralelo ------------------------------------------------------------
def _read_part(path: str, offset: int, size: int) -> bytes:
    with open(path, "rb") as fh:
        fh.seek(offset)
        return fh.read(size)


async def fast_upload(client, file_path: str, workers: int = 8):
    """Envia arquivos grandes em partes paralelas; < 10 MB usa o upload padrão."""
    file_size = os.path.getsize(file_path)
    if file_size < 10 * 1024 * 1024:
        return await client.upload_file(file_path)

    if file_size <= 50 * 1024 * 1024:
        part_size = 128 * 1024
    elif file_size <= 100 * 1024 * 1024:
        part_size = 256 * 1024
    else:
        part_size = 512 * 1024

    part_count = math.ceil(file_size / part_size)
    file_id = int.from_bytes(os.urandom(8), byteorder="big", signed=True)
    pool = asyncio.Semaphore(workers)

    async def upload_part(index: int) -> None:
        async with pool:
            data = await asyncio.to_thread(_read_part, file_path, index * part_size, part_size)
            request = functions.upload.SaveBigFilePartRequest(
                file_id=file_id, file_part=index, file_total_parts=part_count, bytes=data
            )
            await with_server_retry(lambda: client(request), f"parte {index + 1}/{part_count}")

    await asyncio.gather(*(upload_part(i) for i in range(part_count)))
    return types.InputFileBig(id=file_id, parts=part_count, name=os.path.basename(file_path))
