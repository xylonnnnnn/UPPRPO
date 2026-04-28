import imghdr
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile


BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
PINS_DIR = UPLOADS_DIR / "pins"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif", "webp"}
EXTENSION_BY_TYPE = {
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
}


def ensure_upload_dirs() -> None:
    PINS_DIR.mkdir(parents=True, exist_ok=True)


def image_path_to_url(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    normalized = image_path.replace("\\", "/")
    return normalized if normalized.startswith("/") else f"/{normalized}"


def delete_stored_image(image_path: Optional[str]) -> None:
    if not image_path:
        return

    normalized = image_path.lstrip("/").replace("\\", "/")
    file_path = BASE_DIR / normalized
    try:
        file_path.resolve().relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        return

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass


def _detect_image_extension(file_bytes: bytes) -> str:
    image_type = imghdr.what(None, h=file_bytes)
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Поддерживаются только JPG, PNG, GIF и WEBP")
    return EXTENSION_BY_TYPE[image_type]


async def save_upload_file(file: UploadFile) -> str:
    ensure_upload_dirs()
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 10 МБ)")

    extension = _detect_image_extension(file_bytes)
    file_name = f"{uuid.uuid4().hex}{extension}"
    destination = PINS_DIR / file_name
    destination.write_bytes(file_bytes)
    return f"/uploads/pins/{file_name}"
