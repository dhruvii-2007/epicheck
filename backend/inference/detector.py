from ultralytics import YOLO
import numpy as np

class Detector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def predict(self, image: np.ndarray):
        results = self.model(image)[0]

        predictions = []
        for box in results.boxes:
            predictions.append({
                "label": self.model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0]
            })

        return predictions
