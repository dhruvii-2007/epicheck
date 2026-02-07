import time
from fastapi import Request, HTTPException, status

# --------------------------------------------------
# SIMPLE IN-MEMORY RATE LIMITER
# --------------------------------------------------
# Keyed by: IP + PATH
# Window-based (per minute)
# --------------------------------------------------

def rate_limit(limit: int, window: int = 60):
    """
    Rate limit dependency.
    Args:
        limit: number of requests
        window: time window in seconds (default 60s)
    """

    async def limiter(request: Request):
        ip = request.client.host
        path = request.url.path
        key = f"{ip}:{path}"

        now = int(time.time())
        bucket = request.app.state.rate_limit.get(key, [])

        # Remove expired timestamps
        bucket = [t for t in bucket if now - t < window]

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )

        bucket.append(now)
        request.app.state.rate_limit[key] = bucket

    return limiter
