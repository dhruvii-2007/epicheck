# --------------------------------------------------
# API
# --------------------------------------------------

API_VERSION = "v1"


# --------------------------------------------------
# FILE / IMAGE VALIDATION
# --------------------------------------------------

MAX_IMAGE_SIZE_MB = 5

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
}


# --------------------------------------------------
# ROLES (profiles.role)
# --------------------------------------------------

ROLE_USER = "user"
ROLE_DOCTOR = "doctor"
ROLE_ADMIN = "admin"
ROLE_SUPPORT = "support"

ALL_ROLES = {
    ROLE_USER,
    ROLE_DOCTOR,
    ROLE_ADMIN,
    ROLE_SUPPORT,
}


# --------------------------------------------------
# PROFILE STATUS (profiles.status)
# --------------------------------------------------

STATUS_ACTIVE = "active"
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

PROFILE_STATUSES = {
    STATUS_ACTIVE,
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
}


# --------------------------------------------------
# SKIN CASE STATUS (skin_cases.status)
# --------------------------------------------------

CASE_SUBMITTED = "submitted"
CASE_PROCESSING = "processing"
CASE_REVIEWED = "reviewed"
CASE_CLOSED = "closed"

CASE_STATUSES = {
    CASE_SUBMITTED,
    CASE_PROCESSING,
    CASE_REVIEWED,
    CASE_CLOSED,
}


# --------------------------------------------------
# DOCTOR REVIEW DECISIONS
# --------------------------------------------------

REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"
REVIEW_NEEDS_INFO = "needs_more_info"

REVIEW_DECISIONS = {
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    REVIEW_NEEDS_INFO,
}


# --------------------------------------------------
# TICKET STATUS
# --------------------------------------------------

TICKET_OPEN = "open"
TICKET_IN_PROGRESS = "in_progress"
TICKET_RESOLVED = "resolved"
TICKET_CLOSED = "closed"

TICKET_STATUSES = {
    TICKET_OPEN,
    TICKET_IN_PROGRESS,
    TICKET_RESOLVED,
    TICKET_CLOSED,
}


# --------------------------------------------------
# SYSTEM JOB STATUS
# --------------------------------------------------

JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_FAILED = "failed"
JOB_COMPLETED = "completed"

JOB_STATUSES = {
    JOB_PENDING,
    JOB_RUNNING,
    JOB_FAILED,
    JOB_COMPLETED,
}


# --------------------------------------------------
# RATE LIMIT DEFAULTS
# --------------------------------------------------

RATE_LIMIT_USER = 20       # per minute
RATE_LIMIT_DOCTOR = 30
RATE_LIMIT_ADMIN = 10


# --------------------------------------------------
# AUDIT ACTION KEYS
# --------------------------------------------------

AUDIT_AI_PREDICTION = "AI_PREDICTION"
AUDIT_REVIEW_CASE = "REVIEW_CASE"
AUDIT_ASSIGN_CASE = "ASSIGN_CASE"

AUDIT_APPROVE_DOCTOR = "APPROVE_DOCTOR"
AUDIT_REVOKE_DOCTOR = "REVOKE_DOCTOR"
AUDIT_SUSPEND_USER = "SUSPEND_USER"

AUDIT_LOGIN = "LOGIN"
AUDIT_LOGOUT = "LOGOUT"


# --------------------------------------------------
# NOTIFICATION TYPES
# --------------------------------------------------

NOTIFY_SYSTEM = "system"
NOTIFY_CASE = "case"
NOTIFY_ADMIN = "admin"


# --------------------------------------------------
# FEATURE FLAGS (feature_flags.key)
# --------------------------------------------------

FEATURE_AI_ENABLED = "ai_enabled"
FEATURE_DOCTOR_REVIEWS = "doctor_reviews"
FEATURE_NOTIFICATIONS = "notifications"
