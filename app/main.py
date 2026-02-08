from fastapi import FastAPI
from app.routers.health import router as health_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router
from app.routers.notifications import router as notifications_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
app.include_router(notifications_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router
from app.routers.notifications import router as notifications_router
from app.routers.tickets import router as tickets_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
app.include_router(notifications_router)
app.include_router(tickets_router)
from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router
from app.routers.notifications import router as notifications_router
from app.routers.tickets import router as tickets_router
from app.routers.admin import router as admin_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
app.include_router(notifications_router)
app.include_router(tickets_router)
app.include_router(admin_router)
from fastapi import FastAPI
from app.middleware.request_logger import request_logger_middleware

from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.consents import router as consents_router
from app.routers.cases import router as cases_router
from app.routers.ai import router as ai_router
from app.routers.doctors import router as doctors_router
from app.routers.notifications import router as notifications_router
from app.routers.tickets import router as tickets_router
from app.routers.admin import router as admin_router

app = FastAPI(
    title="Epicheck API",
    version="1.0.0"
)

# 🔍 request logging
app.middleware("http")(request_logger_middleware)

# routes
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consents_router)
app.include_router(cases_router)
app.include_router(ai_router)
app.include_router(doctors_router)
app.include_router(notifications_router)
app.include_router(tickets_router)
app.include_router(admin_router)
