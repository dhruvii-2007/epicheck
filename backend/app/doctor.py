from fastapi import Depends, HTTPException
from .auth import get_current_user
from .supabase_client import supabase

def get_current_doctor(current_user=Depends(get_current_user)):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    return current_user


def get_assigned_cases(doctor):
    response = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("assigned_doctor", doctor["id"])
        .execute()
    )
    return response.data
