# app/main.py

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core_logger import logger          # ✅ raw logger
from app.logger import request_log          # ✅ helper only
from app.routers import cases, auth, doctors, notifications, tickets

# --------------------------------------------------
# APP INIT
# --------------------------------------------------

app = FastAPI(
    title="EpiCheck API",
    version="1.0.0"
)

# --------------------------------------------------
# CORS (adjust origins in prod)
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# REQUEST LOGGING MIDDLEWARE
# --------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response: Response = await call_next(request)

    try:
        request_log(
            user_id=request.headers.get("x-user-id"),
            ip_address=request.client.host if request.client else None,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
        )
    except Exception as e:
        logger.error(f"Middleware logging failed: {e}")

    return response

# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])

# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health", tags=["system"])
def health():
    logger.info("Health check OK")
    return {"status": "ok"}
