from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
import time

from .config import API_VERSION
from .logger import logger

# Routers
from .routes.user import router as user_router
from .routes.doctor import router as doctor_router
from .routes.admin import router as admin_router
from .routes.tickets import router as tickets_router

# System
from .system.notifications import router as notifications_router
from .system.feature_flags import router as feature_flags_router

# Rate limiting
from .ratelimit import init_rate_limit_state

load_dotenv()

app = FastAPI(
    title="Epicheck API",
    version=API_VERSION,
    description="Epicheck backend — secure, audited medical AI platform"
)

security = HTTPBearer()

# --------------------------------------------------
# CORS (LOCKED TO FRONTEND)
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://epicheck.great-site.net",
        "https://epicheck.great-site.net"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
# REQUEST LOGGING (request_logs table)
# --------------------------------------------------
@app.middleware("http")
async def request_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round(time.time() - start_time, 3)

    try:
        from .supabase_client import db_insert

        db_insert(
            "request_logs",
            {
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "ip_address": request.client.host if request.client else None
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
# ROUTERS
# --------------------------------------------------
app.include_router(
    user_router,
    prefix=f"/{API_VERSION}",
    tags=["User"]
)

app.include_router(
    doctor_router,
    prefix=f"/{API_VERSION}/doctor",
    tags=["Doctor"]
)

app.include_router(
    admin_router,
    prefix=f"/{API_VERSION}/admin",
    tags=["Admin"]
)

app.include_router(
    tickets_router,
    prefix=f"/{API_VERSION}/tickets",
    tags=["Support"]
)

app.include_router(
    notifications_router,
    prefix=f"/{API_VERSION}/notifications",
    tags=["Notifications"]
)

app.include_router(
    feature_flags_router,
    prefix=f"/{API_VERSION}/features",
    tags=["Feature Flags"]
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
