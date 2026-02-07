import random
from datetime import datetime
from .supabase_client import db_select, db_insert

DISEASE_LABELS = [
    "melanoma",
    "nevus",
    "seborrheic_keratosis",
    "basal_cell_carcinoma",
    "benign"
]

def get_active_model():
    return db_select(
        "ai_models",
        filters={"is_active": True},
        single=True
    )

def predict_and_store(*, case_id: str):
    model = get_active_model()
    if not model:
        raise RuntimeError("No active AI model")

    predictions = []

    for label in DISEASE_LABELS:
        confidence = round(random.uniform(0.01, 0.99), 2)
        predictions.append({
            "case_id": case_id,
            "model_id": model["id"],
            "label": label,
            "confidence": confidence,
            "bbox": None,
            "created_at": datetime.utcnow().isoformat()
        })

    for p in predictions:
        db_insert("case_predictions", p)

    top = max(predictions, key=lambda x: x["confidence"])
    return top["label"], top["confidence"], model["id"]
