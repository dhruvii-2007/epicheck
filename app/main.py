from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime
import time

from app.config import API_VERSION
from app.logger import logger

# Routers
from app.routes.user import router as user_router
from app.routes.doctor import router as doctor_router
from app.routes.admin import router as admin_router
from app.routes.tickets import router as tickets_router

# System
from app.system.notifications import router as notifications_router
from app.system.feature_flags import router as feature_flags_router

# Rate limiting
from app.ratelimit import init_rate_limit_state

load_dotenv()

app = FastAPI(
    title="Epicheck API",
    version=API_VERSION,
    description="Epicheck backend — secure, audited medical AI platform"
)

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://epicheck.great-site.net",
        "https://epicheck.great-site.net"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# --------------------------------------------------
# STARTUP
# --------------------------------------------------
@app.on_event("startup")
def startup():
    init_rate_limit_state(app)
    logger.info("Epicheck API started")

# --------------------------------------------------
# REQUEST LOGGING
# --------------------------------------------------
@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 3)

    try:
        from app.supabase_client import db_insert

        db_insert(
            table="request_logs",
            payload={
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "ip_address": request.client.host if request.client else None,
                "created_at": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Request log failed: {e}")

    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {duration}s"
    )

    return response

# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------------------------------------
# ROUTERS (NO DOUBLE PREFIXES)
# --------------------------------------------------
app.include_router(
    user_router,
    prefix=f"/{API_VERSION}"
)

app.include_router(
    doctor_router,
    prefix=f"/{API_VERSION}"
)

app.include_router(
    admin_router,
    prefix=f"/{API_VERSION}"
)

app.include_router(
    tickets_router,
    prefix=f"/{API_VERSION}"
)

app.include_router(
    notifications_router,
    prefix=f"/{API_VERSION}"
)

app.include_router(
    feature_flags_router,
    prefix=f"/{API_VERSION}"
)

# --------------------------------------------------
# GLOBAL ERROR HANDLER
# --------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
