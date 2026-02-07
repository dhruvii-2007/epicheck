import datetime

from app.supabase_client import (
    db_select,
    db_insert,
    db_update
)
from app.logger import logger
from app.config import (
    CASE_SUBMITTED,
    CASE_PROCESSING,
    NOTIFY_CASE,
    NOTIFY_SYSTEM,
    NOTIFY_ADMIN
)

# --------------------------------------------------
# REMINDER CONFIG
# --------------------------------------------------

REVIEW_REMINDER_HOURS = 24
UNASSIGNED_REMINDER_HOURS = 12
JOB_NAME = "send_reminders"

# --------------------------------------------------
# REMINDER JOB
# --------------------------------------------------

def send_reminders():
    """
    Sends reminder notifications for:
    - Unassigned skin cases (admins)
    - Pending doctor reviews (assigned doctor)

    DB effects:
    - notifications insert
    - audit_logs insert
    - cron_health UPSERT-safe update
    """

    now = datetime.datetime.utcnow()
    job_started_at = now.isoformat()

    try:
        # --------------------------------------------------
        # UNASSIGNED CASE REMINDERS (ADMIN)
        # --------------------------------------------------

        unassigned_cases = db_select(
            table="skin_cases",
            filters={
                "status": CASE_SUBMITTED,
                "assigned_doctor": None,
                "deleted_at": None
            }
        )

        admins = db_select(
            table="profiles",
            filters={"role": "admin"}
        )

        for case in unassigned_cases:
            created_at = datetime.datetime.fromisoformat(case["created_at"])
            age_hours = (now - created_at).total_seconds() / 3600

            if age_hours < UNASSIGNED_REMINDER_HOURS:
                continue

            for admin in admins:
                db_insert(
                    table="notifications",
                    payload={
                        "user_id": admin["id"],
                        "title": "Unassigned Case Pending",
                        "message": (
                            f"Skin case {case['id']} has not been assigned "
                            f"for over {UNASSIGNED_REMINDER_HOURS} hours."
                        ),
                        "type": NOTIFY_ADMIN,
                        "action_url": f"/admin/cases/{case['id']}",
                        "is_read": False,
                        "created_at": job_started_at
                    }
                )

        # --------------------------------------------------
        # PENDING REVIEW REMINDERS (DOCTOR)
        # --------------------------------------------------

        pending_cases = db_select(
            table="skin_cases",
            filters={
                "status": CASE_PROCESSING,
                "deleted_at": None
            }
        )

        for case in pending_cases:
            if not case.get("assigned_doctor"):
                continue

            updated_at = datetime.datetime.fromisoformat(
                case.get("updated_at") or case["created_at"]
            )
            age_hours = (now - updated_at).total_seconds() / 3600

            if age_hours < REVIEW_REMINDER_HOURS:
                continue

            db_insert(
                table="notifications",
                payload={
                    "user_id": case["assigned_doctor"],
                    "title": "Pending Case Review",
                    "message": (
                        f"You have a skin case pending review "
                        f"for over {REVIEW_REMINDER_HOURS} hours."
                    ),
                    "type": NOTIFY_CASE,
                    "action_url": f"/doctor/cases/{case['id']}",
                    "is_read": False,
                    "created_at": job_started_at
                }
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

        logger.info("Reminder job completed successfully")

    except Exception as e:
        logger.critical(f"Reminder job crashed: {e}")

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
