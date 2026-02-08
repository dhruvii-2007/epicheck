from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import ENVIRONMENT
from app.supabase_client import supabase

# middleware
from app.middleware.request_logger import request_logger_middleware

# routers
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router
from app.routers.notifications import router as notifications_router
from app.routers.tickets import router as tickets_router
from app.routers.admin import router as admin_router


# --------------------------------------------------
# Lifespan (startup / shutdown)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: fail fast if Supabase is unreachable
    try:
        supabase.table("feature_flags").select("key").limit(1).execute()
    except Exception as e:
        raise RuntimeError("Supabase connection failed") from e

    yield

    # Shutdown (optional cleanup later)


# --------------------------------------------------
# App
# --------------------------------------------------
app = FastAPI(
    title="Epicheck API",
    version="1.0.0",
    lifespan=lifespan
)


# --------------------------------------------------
# CORS
# --------------------------------------------------
if ENVIRONMENT == "production":
    allowed_origins = [
        "https://epicheck.great-site.net"
    ]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request logging
# --------------------------------------------------
app.middleware("http")(request_logger_middleware)


# --------------------------------------------------
# Routes
# --------------------------------------------------
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
app.include_router(notifications_router)
app.include_router(tickets_router)
app.include_router(admin_router)


# --------------------------------------------------
# Root (sanity check)
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "name": "Epicheck API",
        "environment": ENVIRONMENT,
        "status": "running"
    }
