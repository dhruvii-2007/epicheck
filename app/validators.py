from fastapi import UploadFile, HTTPException
from .config import MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_TYPES

# --------------------------------------------------
# IMAGE VALIDATION
# --------------------------------------------------

def validate_image(file: UploadFile, size_bytes: int):
    """
    Validates uploaded medical image.
    Checks:
    - MIME type
    - File size
    """

    # MIME type check
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Only JPG and PNG are allowed."
        )

    # Size check
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds {MAX_IMAGE_SIZE_MB}MB size limit."
        )
