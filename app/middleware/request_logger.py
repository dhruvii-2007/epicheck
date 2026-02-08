from datetime import datetime
from fastapi import Request
from app.supabase_client import supabase

# Paths we do NOT want to log (noise)
EXCLUDED_PATHS = {"/health"}
EXCLUDED_METHODS = {"OPTIONS"}


async def request_logger_middleware(request: Request, call_next):
    # Skip noisy requests early
    if request.method in EXCLUDED_METHODS or request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    start_time = datetime.utcnow()

    response = await call_next(request)

    duration_ms = int(
        (datetime.utcnow() - start_time).total_seconds() * 1000
    )

    try:
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("id")

        supabase.table("request_logs").insert({
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id,
            "created_at": start_time.isoformat()
        }).execute()

    except Exception:
        # Logging must NEVER break request handling
        # Fail silently by design
        pass

    return response
