from app.supabase_client import supabase

def send_notification_digests():
    users = (
        supabase
        .table("notifications")
        .select("user_id")
        .eq("read", False)
        .execute()
        .data
    )

    user_ids = set(u["user_id"] for u in users)

    for user_id in user_ids:
        unread_count = len([
            n for n in users if n["user_id"] == user_id
        ])

        # placeholder for email / push
        supabase.table("notifications").update({
            "digest_sent": True
        }).eq("user_id", user_id).execute()


if __name__ == "__main__":
    send_notification_digests()
