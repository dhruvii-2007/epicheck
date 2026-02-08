from datetime import datetime
from fastapi import Request
from app.supabase_client import supabase

async def request_logger_middleware(request: Request, call_next):
    start_time = datetime.utcnow()

    response = await call_next(request)

    try:
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("id")

        supabase.table("request_logs").insert({
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id,
            "created_at": start_time.isoformat()
        }).execute()
    except Exception:
        # never break request flow because of logging
        pass

    return response
