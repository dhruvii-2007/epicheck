from datetime import datetime, timedelta
from app.supabase_client import supabase

ORPHAN_IMAGE_DAYS = 7

def cleanup_images():
    cutoff = (datetime.utcnow() - timedelta(days=ORPHAN_IMAGE_DAYS)).isoformat()

    files = (
        supabase
        .table("case_files")
        .select("id, storage_path")
        .is_("case_id", None)
        .lt("created_at", cutoff)
        .execute()
        .data
    )

    for f in files:
        try:
            supabase.storage.from_("case-images").remove([f["storage_path"]])
            supabase.table("case_files").delete().eq("id", f["id"]).execute()
        except Exception:
            pass


if __name__ == "__main__":
    cleanup_images()
