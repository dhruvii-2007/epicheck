from ultralytics import YOLO
import numpy as np
from config import MODEL_PATH, CONFIDENCE_THRESHOLD

class Detector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def predict(self, image: np.ndarray):
        results = self.model(
            image,
            imgsz=640,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False
        )[0]

        predictions = []

        if results.boxes is None:
            return predictions

        for box in results.boxes:
            predictions.append({
                "label": self.model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": [float(x) for x in box.xyxy[0]]
            })

        return predictions
