from supabase_client import supabase

def create_case(user_id, image_url, ai_result, confidence, severity, risk, action):
    data = {
        "user_id": user_id,
        "image_url": image_url,
        "ai_result": ai_result,
        "ai_confidence": confidence,
        "severity_score": severity,
        "risk_level": risk,
        "action_plan": action
    }
    response = supabase.table("skin_cases").insert(data).execute()
    return response.data[0]
