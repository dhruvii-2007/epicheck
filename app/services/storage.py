from app.supabase_client import supabase

SIGNED_URL_TTL = 300  # seconds

def get_signed_image_url(path: str) -> str:
    res = supabase.storage.from_("case-images").create_signed_url(
        path,
        SIGNED_URL_TTL
    )
    return res.get("signedURL")
