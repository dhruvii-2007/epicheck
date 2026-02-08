from app.supabase_client import supabase

MAX_RETRIES = 3

def retry_failed_ai():
    cases = (
        supabase
        .table("skin_cases")
        .select("id, ai_retry_count")
        .eq("status", "failed")
        .lt("ai_retry_count", MAX_RETRIES)
        .execute()
        .data
    )

    for case in cases:
        supabase.table("skin_cases").update({
            "status": "submitted",
            "ai_retry_count": case["ai_retry_count"] + 1
        }).eq("id", case["id"]).execute()


if __name__ == "__main__":
    retry_failed_ai()
