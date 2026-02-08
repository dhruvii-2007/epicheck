from fastapi import FastAPI
from app.routers import cases, uploads, doctor, admin

app = FastAPI(title="Epicheck API", version="1.0")

app.include_router(cases.router)
app.include_router(uploads.router)
app.include_router(doctor.router)
app.include_router(admin.router)
