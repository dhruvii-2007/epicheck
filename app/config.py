# app/config.py
from datetime import timedelta

# --------------------------------------------------
# CASE STATUS (skin_cases.status)
# CHECK constraint enforced in DB
# --------------------------------------------------
CASE_SUBMITTED = "submitted"
CASE_PROCESSING = "processing"
CASE_REVIEWED = "reviewed"
CASE_CLOSED = "closed"

VALID_CASE_STATUSES = {
    CASE_SUBMITTED,
    CASE_PROCESSING,
    CASE_REVIEWED,
    CASE_CLOSED,
}

# --------------------------------------------------
# DOCTOR REVIEW DECISIONS (doctor_reviews.decision)
# --------------------------------------------------
REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"
REVIEW_NEEDS_MORE_INFO = "needs_more_info"

VALID_REVIEW_DECISIONS = {
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    REVIEW_NEEDS_MORE_INFO,
}

# --------------------------------------------------
# USER / PROFILE ROLES (profiles.role)
# --------------------------------------------------
ROLE_USER = "user"
ROLE_DOCTOR = "doctor"
ROLE_ADMIN = "admin"
ROLE_SUPPORT = "support"

VALID_ROLES = {
    ROLE_USER,
    ROLE_DOCTOR,
    ROLE_ADMIN,
    ROLE_SUPPORT,
}

# --------------------------------------------------
# PROFILE STATUS (profiles.status)
# --------------------------------------------------
PROFILE_ACTIVE = "active"
PROFILE_PENDING = "pending"
PROFILE_APPROVED = "approved"
PROFILE_REJECTED = "rejected"

VALID_PROFILE_STATUSES = {
    PROFILE_ACTIVE,
    PROFILE_PENDING,
    PROFILE_APPROVED,
    PROFILE_REJECTED,
}

# --------------------------------------------------
# TICKET STATUS (tickets.status)
# --------------------------------------------------
TICKET_OPEN = "open"
TICKET_IN_PROGRESS = "in_progress"
TICKET_RESOLVED = "resolved"
TICKET_CLOSED = "closed"

VALID_TICKET_STATUSES = {
    TICKET_OPEN,
    TICKET_IN_PROGRESS,
    TICKET_RESOLVED,
    TICKET_CLOSED,
}

# --------------------------------------------------
# SYSTEM JOB STATUS (system_jobs.status)
# --------------------------------------------------
JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_FAILED = "failed"
JOB_COMPLETED = "completed"

VALID_JOB_STATUSES = {
    JOB_PENDING,
    JOB_RUNNING,
    JOB_FAILED,
    JOB_COMPLETED,
}

# --------------------------------------------------
# NOTIFICATION TYPES (notifications.type)
# --------------------------------------------------
NOTIFY_CASE = "case"
NOTIFY_SYSTEM = "system"

# --------------------------------------------------
# LOG RETENTION (mirrors DB defaults)
# --------------------------------------------------
REQUEST_LOG_RETENTION = timedelta(days=90)
AUDIT_LOG_RETENTION = timedelta(days=365)
