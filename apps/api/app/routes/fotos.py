"""Serve fotos dos docentes em data/fotos."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.professor_foto import FOTO_EXTENSIONS, fotos_dir

router = APIRouter(prefix="/fotos", tags=["Fotos"])

_MEDIA_TYPES = {
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@router.get("/{filename}")
async def serve_foto(filename: str):
    """Retorna arquivo de foto (ex.: camilla.gif)."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    base = fotos_dir()
    path = base / filename
    if not path.is_file():
        stem = Path(filename).stem.lower()
        for ext in FOTO_EXTENSIONS:
            candidate = base / f"{stem}{ext}"
            if candidate.is_file():
                path = candidate
                break
        else:
            raise HTTPException(status_code=404, detail="Foto não encontrada")

    media = _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media)
