import datetime
from app.supabase_client import (
    db_select,
    db_update
)
from app.logger import logger

# --------------------------------------------------
# CLEANUP CONFIG
# --------------------------------------------------

MAX_RETRIES = 3


# --------------------------------------------------
# CLEANUP JOB
# --------------------------------------------------

def cleanup_case_files():
    """
    Cleans up case_files marked for deletion.
    Updates:
    - storage_cleaned
    - cleanup_attempts
    - cleanup_failed
    - deleted_at
    """

    job_started_at = datetime.datetime.utcnow()

    try:
        files = db_select(
            table="case_files",
            filters={
                "marked_for_deletion": True,
                "storage_cleaned": False
            }
        )

        for file in files:
            file_id = file["id"]
            attempts = file.get("cleanup_attempts", 0)

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
                # STORAGE DELETE (SUPABASE HANDLED SEPARATELY)
                # -----------------------------------------
                # We assume Supabase storage lifecycle / webhook
                # handles actual file deletion.

                db_update(
                    table="case_files",
                    payload={
                        "storage_cleaned": True,
                        "deleted_at": job_started_at.isoformat()
                    },
                    filters={"id": file_id}
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
        # CRON HEALTH SUCCESS
        # --------------------------------------------------

        db_update(
            table="cron_health",
            payload={
                "job_name": "cleanup_case_files",
                "status": "success",
                "ran_at": job_started_at.isoformat()
            },
            filters={}
        )

        logger.info("Cleanup job completed successfully")

    except Exception as e:
        logger.critical(f"Cleanup job crashed: {e}")

        db_update(
            table="cron_health",
            payload={
                "job_name": "cleanup_case_files",
                "status": "failed",
                "error": str(e),
                "ran_at": job_started_at.isoformat()
            },
            filters={}
        )
