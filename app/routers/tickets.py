from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.core.dependencies import get_current_user
from app.core.roles import require_support_or_admin
from app.supabase_client import supabase
from app.services.notifications import create_notification
from app.services.audit import log_audit_event

router = APIRouter(prefix="/tickets", tags=["Support & Tickets"])


# --------------------------------------------------
# CREATE TICKET
# --------------------------------------------------
@router.post("")
def create_ticket(
    payload: dict,
    profile=Depends(get_current_user)
):
    """
    User creates a support ticket
    """

    subject = payload.get("subject")
    message = payload.get("message")

    if not subject or not message:
        raise HTTPException(
            status_code=400,
            detail="subject and message required"
        )

    resp = supabase.table("tickets").insert({
        "user_id": profile["id"],
        "subject": subject,
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Ticket creation failed")

    ticket = resp.data[0]

    # first message
    supabase.table("ticket_messages").insert({
        "ticket_id": ticket["id"],
        "sender_id": profile["id"],
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    log_audit_event(
        actor_id=profile["id"],
        action="ticket_created",
        target_table="tickets",
        target_id=ticket["id"]
    )

    return ticket


# --------------------------------------------------
# LIST TICKETS
# --------------------------------------------------
@router.get("")
def list_tickets(
    page: int = 1,
    limit: int = 20,
    profile=Depends(get_current_user)
):
    """
    User: own tickets
    Support/Admin: all tickets
    """

    if limit > 50:
        limit = 50

    offset = (page - 1) * limit

    query = (
        supabase
        .table("tickets")
        .select("*", count="exact")
        .is_("deleted_at", None)
    )

    if profile["role"] not in ["support", "admin"]:
        query = query.eq("user_id", profile["id"])

    resp = (
        query
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "page": page,
        "limit": limit,
        "total": resp.count,
        "tickets": resp.data or []
    }


# --------------------------------------------------
# GET TICKET DETAILS
# --------------------------------------------------
@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    profile=Depends(get_current_user)
):
    """
    Get ticket with messages
    """

    ticket_query = (
        supabase
        .table("tickets")
        .select("*")
        .eq("id", ticket_id)
        .is_("deleted_at", None)
    )

    if profile["role"] not in ["support", "admin"]:
        ticket_query = ticket_query.eq("user_id", profile["id"])

    ticket_resp = ticket_query.limit(1).execute()

    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_resp.data[0]

    messages = (
        supabase
        .table("ticket_messages")
        .select("*")
        .eq("ticket_id", ticket_id)
        .is_("deleted_at", None)
        .order("created_at")
        .execute()
    ).data or []

    return {
        "ticket": ticket,
        "messages": messages
    }


# --------------------------------------------------
# ADD MESSAGE
# --------------------------------------------------
@router.post("/{ticket_id}/message")
def add_ticket_message(
    ticket_id: str,
    payload: dict,
    profile=Depends(get_current_user)
):
    """
    Add a message to a ticket
    """

    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message required")

    ticket_query = (
        supabase
        .table("tickets")
        .select("*")
        .eq("id", ticket_id)
        .is_("deleted_at", None)
    )

    if profile["role"] not in ["support", "admin"]:
        ticket_query = ticket_query.eq("user_id", profile["id"])

    ticket_resp = ticket_query.limit(1).execute()

    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_resp.data[0]

    supabase.table("ticket_messages").insert({
        "ticket_id": ticket_id,
        "sender_id": profile["id"],
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    log_audit_event(
        actor_id=profile["id"],
        action="ticket_message_added",
        target_table="ticket_messages",
        target_id=ticket_id
    )

    # notify user if support/admin replied
    if profile["role"] in ["support", "admin"]:
        create_notification(
            user_id=ticket["user_id"],
            title="Support replied",
            message="You received a reply on your support ticket.",
            notif_type="ticket_reply",
            action_url=f"/tickets/{ticket_id}"
        )

    return {"status": "message_sent"}


# --------------------------------------------------
# UPDATE TICKET STATUS
# --------------------------------------------------
@router.put("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    payload: dict,
    support=Depends(require_support_or_admin)
):
    """
    Update ticket status (support/admin only)
    """

    new_status = payload.get("status")
    allowed = ["open", "in_progress", "resolved", "closed"]

    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    resp = (
        supabase
        .table("tickets")
        .update({
            "status": new_status,
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", ticket_id)
        .is_("deleted_at", None)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    log_audit_event(
        actor_id=support["id"],
        action="ticket_status_updated",
        target_table="tickets",
        target_id=ticket_id,
        metadata={"status": new_status}
    )

    return {"status": "updated"}
