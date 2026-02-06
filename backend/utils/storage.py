import uuid
from supabase_client import supabase
from config import STORAGE_BUCKET

def upload_case_image(user_id: str, file_bytes: bytes, filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    path = f"{user_id}/{uuid.uuid4()}.{ext}"

    supabase.storage.from_(STORAGE_BUCKET).upload(
        path=path,
        file=file_bytes,
        file_options={
            "content-type": f"image/{ext}",
            "upsert": False
        }
    )

    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(path)
