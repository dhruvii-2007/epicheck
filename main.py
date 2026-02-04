from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI(
    title="Epicheck AI Detection API",
    version="1.0"
)

# Load YOLOv8 detection model
model = YOLO("models/epicheck_detect.pt")

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
                "y2": round(y2, 2)
            }
        })

    return {
        "count": len(detections),
        "detections": detections
    }
