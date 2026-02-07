from fastapi import UploadFile, HTTPException
from .config import MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_TYPES

def validate_image(file: UploadFile, size_bytes: int):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Only JPG and PNG allowed."
        )

    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds {MAX_IMAGE_SIZE_MB}MB limit."
        )
