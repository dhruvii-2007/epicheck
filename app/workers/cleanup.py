import datetime

from app.supabase_client import (
    db_select,
    db_update,
    db_insert
)
from app.logger import logger

# --------------------------------------------------
# CLEANUP CONFIG
# --------------------------------------------------

MAX_RETRIES = 3
JOB_NAME = "cleanup_case_files"

# --------------------------------------------------
# CLEANUP JOB
# --------------------------------------------------

def cleanup_case_files():
    """
    Cleans up case_files marked for deletion.

    DB effects:
    - storage_cleaned = true
    - cleanup_attempts incremented
    - cleanup_failed set after max retries
    - deleted_at set
    - audit_logs entry created
    - cron_health updated (UPSERT-safe)
    """

    job_started_at = datetime.datetime.utcnow().isoformat()

    try:
        files = db_select(
            table="case_files",
            filters={
                "marked_for_deletion": True,
                "storage_cleaned": False,
                "cleanup_failed": False
            }
        )

        for file in files:
            file_id = file["id"]
            attempts = file.get("cleanup_attempts", 0)

            # -----------------------------------------
            # MAX RETRIES REACHED
            # -----------------------------------------
            if attempts >= MAX_RETRIES:
                db_update(
                    table="case_files",
                    payload={
                        "cleanup_failed": True
                    },
                    filters={"id": file_id}
                )
                continue

            try:
                # -----------------------------------------
                # STORAGE DELETE
                # -----------------------------------------
                # Actual file deletion handled by Supabase
                # storage lifecycle / webhook

                db_update(
                    table="case_files",
                    payload={
                        "storage_cleaned": True,
                        "cleanup_attempts": attempts + 1,
                        "deleted_at": job_started_at
                    },
                    filters={"id": file_id}
                )

                # -----------------------------------------
                # AUDIT LOG
                # -----------------------------------------
                db_insert(
                    table="audit_logs",
                    payload={
                        "actor_id": None,
                        "actor_role": "system",
                        "action": "CLEANUP_CASE_FILE",
                        "details": {
                            "file_id": file_id
                        },
                        "created_at": job_started_at
                    }
                )

            except Exception as file_error:
                logger.error(f"Cleanup failed for file {file_id}: {file_error}")

                db_update(
                    table="case_files",
                    payload={
                        "cleanup_attempts": attempts + 1
                    },
                    filters={"id": file_id}
                )

        # --------------------------------------------------
        # CRON HEALTH — SUCCESS (UPSERT SAFE)
        # --------------------------------------------------
        existing = db_select(
            table="cron_health",
            filters={"job_name": JOB_NAME},
            single=True
        )

        if existing:
            db_update(
                table="cron_health",
                payload={
                    "status": "success",
                    "ran_at": job_started_at
                },
                filters={"job_name": JOB_NAME}
            )
        else:
            db_insert(
                table="cron_health",
                payload={
                    "job_name": JOB_NAME,
                    "status": "success",
                    "ran_at": job_started_at
                }
            )

        logger.info("Cleanup job completed successfully")

    except Exception as e:
        logger.critical(f"Cleanup job crashed: {e}")

        # --------------------------------------------------
        # CRON HEALTH — FAILED (UPSERT SAFE)
        # --------------------------------------------------
        existing = db_select(
            table="cron_health",
            filters={"job_name": JOB_NAME},
            single=True
        )

        if existing:
            db_update(
                table="cron_health",
                payload={
                    "status": "failed",
                    "error": str(e),
                    "ran_at": job_started_at
                },
                filters={"job_name": JOB_NAME}
            )
        else:
            db_insert(
                table="cron_health",
                payload={
                    "job_name": JOB_NAME,
                    "status": "failed",
                    "error": str(e),
                    "ran_at": job_started_at
                }
            )
