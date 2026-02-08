# app/main.py

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.logger import logger, request_log
from app.routers import auth, cases, doctors, notifications, tickets

# --------------------------------------------------
# APP INIT
# --------------------------------------------------

app = FastAPI(
    title="EpiCheck API",
    version="1.0.0",
)

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# REQUEST LOGGING
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
        logger.error(f"Request logging failed: {e}")

    return response

# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(cases, prefix="/cases", tags=["cases"])
app.include_router(doctors, prefix="/doctors", tags=["doctors"])
app.include_router(notifications, prefix="/notifications", tags=["notifications"])
app.include_router(tickets, prefix="/tickets", tags=["tickets"])

# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}
