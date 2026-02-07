from fastapi import HTTPException
from datetime import datetime

from ..supabase_client import (
    db_select,
    db_insert,
    db_update
)

# --------------------------------------------------
# GET ALL FEATURE FLAGS
# --------------------------------------------------
def get_all_feature_flags():
    return db_select(table="feature_flags")

# --------------------------------------------------
# GET SINGLE FEATURE FLAG
# --------------------------------------------------
def get_feature_flag(key: str):
    flag = db_select(
        table="feature_flags",
        filters={"key": key},
        single=True
    )

    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    return flag

# --------------------------------------------------
# CHECK FEATURE ENABLED (RUNTIME USE)
# --------------------------------------------------
def is_feature_enabled(key: str) -> bool:
    flag = db_select(
        table="feature_flags",
        filters={"key": key},
        single=True
    )

    return bool(flag and flag.get("enabled"))

# --------------------------------------------------
# CREATE FEATURE FLAG (ADMIN SERVICE)
# --------------------------------------------------
def create_feature_flag(
    *,
    key: str,
    enabled: bool = False,
    description: str | None = None
):
    existing = db_select(
        table="feature_flags",
        filters={"key": key},
        single=True
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Feature flag already exists"
        )

    return db_insert(
        table="feature_flags",
        payload={
            "key": key,
            "enabled": enabled,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
    )

# --------------------------------------------------
# UPDATE FEATURE FLAG (ADMIN SERVICE)
# --------------------------------------------------
def update_feature_flag(
    *,
    key: str,
    enabled: bool | None = None,
    description: str | None = None
):
    payload = {
        "updated_at": datetime.utcnow().isoformat()
    }

    if enabled is not None:
        payload["enabled"] = enabled

    if description is not None:
        payload["description"] = description

    if len(payload) == 1:
        raise HTTPException(
            status_code=400,
            detail="Nothing to update"
        )

    updated = db_update(
        table="feature_flags",
        payload=payload,
        filters={"key": key}
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Feature flag not found"
        )

    return updated[0]
