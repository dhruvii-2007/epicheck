from app.ai.runtime import get_session
from app.ai.preprocessing import preprocess_image
from app.ai.postprocessing import postprocess
from app.supabase_client import supabase

def run_inference(case_id: str):
    # 1. Fetch case + image
    case = supabase.table("skin_cases").select("*").eq("id", case_id).single().execute()
    image_path = case.data["image_url"]

    # 2. Fetch active model
    model = (
        supabase.table("ai_models")
        .select("*")
        .eq("is_active", True)
        .single()
        .execute()
    ).data

    model_path = f"app/ai/models/epicheck.onnx"

    # 3. Run ONNX
    session = get_session(model_path)
    input_tensor = preprocess_image(image_path)
    outputs = session.run(None, {"input": input_tensor})

    result = postprocess(outputs)

    # 4. Persist prediction
    supabase.table("case_predictions").insert({
        "case_id": case_id,
        "label": result["label"],
        "confidence": result["confidence"],
        "model_id": model["id"]
    }).execute()

    # 5. Cache summary on skin_cases
    supabase.table("skin_cases").update({
        "ai_primary_label": result["label"],
        "ai_confidence": result["confidence"],
        "status": "reviewed"
    }).eq("id", case_id).execute()
