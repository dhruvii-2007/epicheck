from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from .config import API_VERSION
from .supabase_client import supabase
from .inference import predict_stub
from .validators import validate_image
from .logger import logger
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(
    title="Epicheck Backend",
    version=API_VERSION
)

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------------- PREDICT API ----------------
@app.post(f"/{API_VERSION}/predict")
async def predict(
    file: UploadFile = File(...),
    user_email: str = Form(...)
):
    try:
        contents = await file.read()
        validate_image(file, len(contents))

        # AI prediction (stub for now)
        disease, confidence = predict_stub()

        # Insert into Supabase
        response = supabase.table("reports").insert({
            "user_email": user_email,
            "disease": disease,
            "confidence": confidence
        }).execute()

        logger.info(f"Prediction stored for {user_email}")

        return {
            "success": True,
            "disease": disease,
            "confidence": confidence
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
