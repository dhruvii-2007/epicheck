from fastapi import Header, HTTPException
from app.supabase import supabase

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    res = supabase.auth.get_user(token)

    if not res or not res.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    profile = (
        supabase.table("profiles")
        .select("role, is_suspended")
        .eq("id", res.user.id)
        .single()
        .execute()
        .data
    )

    if profile["is_suspended"]:
        raise HTTPException(status_code=403, detail="Account suspended")

    return {
        "id": res.user.id,
        "role": profile["role"]
    }
