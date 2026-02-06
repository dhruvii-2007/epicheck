import config  # FORCE env load first (do not remove)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import tempfile
import os

from supabase_client import supabase
from detector import Detector

app = FastAPI(title="Epicheck API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = Detector()

@app.get("/")
def health():
    return {"status": "Epicheck backend running"}

@app.post("/api/v1/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        image = cv2.imread(tmp_path)
        os.unlink(tmp_path)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        predictions = detector.predict(image)

        return {
            "success": True,
            "predictions": predictions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
