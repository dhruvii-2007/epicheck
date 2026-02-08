from fastapi import Request, HTTPException
import time

WINDOW = 60
MAX_REQUESTS = 100
_store = {}

def rate_limit(request: Request):
    ip = request.client.host
    now = int(time.time())

    bucket = _store.get(ip, [])
    bucket = [t for t in bucket if t > now - WINDOW]

    if len(bucket) >= MAX_REQUESTS:
        raise HTTPException(429, "Rate limit exceeded")

    bucket.append(now)
    _store[ip] = bucket
