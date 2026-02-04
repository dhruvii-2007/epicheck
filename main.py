from fastapi import FastAPI, UploadFile, File
from PIL import Image
from ultralytics import YOLO
import io
import os
import urllib.request

# ---------------- CONFIG ----------------
MODEL_DIR = "models"
MODEL_NAME = "epicheck_detect.pt"

# Direct file URL (NO GitHub API calls)
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"

MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
# ----------------------------------------

app = FastAPI(title="Epicheck Detection API")

# Disable Ultralytics auto-update & GitHub checks
os.environ["ULTRALYTICS_SETTINGS"] = "False"

# Ensure models directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Download model if missing
if not os.path.exists(MODEL_PATH):
    print("⬇️ Downloading YOLO model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("✅ Model downloaded")

# Load model AFTER file exists
print("🚀 Loading YOLO model...")
model = YOLO(MODEL_PATH)
print("✅ Model loaded successfully")


@app.get("/")
def health():
    return {"status": "Epicheck Detection API is running"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = model(image, conf=0.25)

    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        cls_name = model.names[cls_id]
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append({
            "class": cls_name,
            "confidence": round(conf, 4),
            "bbox": {
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2),
            }
        })

    return {
        "count": len(detections),
        "detections": detections
    }
