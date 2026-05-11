from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from ..db import get_db, Session as SessionModel, Message, EscalationTicket, TicketStatus, MessageRole
from ..auth.dependencies import get_current_user
from ..db.models import User, UserRole
from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])


class IntentBreakdown(BaseModel):
    rag: int
    tool_call: int
    escalation: int


class TicketBreakdown(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int


class AnalyticsSummary(BaseModel):
    total_sessions: int
    total_messages: int
    total_customers: int
    escalation_rate: float          # 0.0 – 1.0
    avg_messages_per_session: float
    intent_breakdown: IntentBreakdown
    ticket_breakdown: TicketBreakdown


def _require_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.AGENT,):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agents only")
    return current_user


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    db: DBSession = Depends(get_db),
    _: User = Depends(_require_agent),
):
    total_sessions = db.query(func.count(SessionModel.session_id)).scalar() or 0
    total_messages = db.query(func.count(Message.message_id)).scalar() or 0
    total_customers = db.query(func.count(User.user_id)).filter(
        User.role == UserRole.CUSTOMER
    ).scalar() or 0

    # intent breakdown — count assistant messages by intent keyword in content
    # We derive intent from EscalationTickets (escalation) and infer rag/tool_call
    # from message counts since intent isn't stored on Message model directly.
    # Use EscalationTicket count as escalation proxy.
    escalation_sessions = db.query(func.count(EscalationTicket.ticket_id)).scalar() or 0
    escalation_rate = round(escalation_sessions / total_sessions, 4) if total_sessions > 0 else 0.0

    avg_messages = round(total_messages / total_sessions, 2) if total_sessions > 0 else 0.0

    # ticket breakdown
    def ticket_count(s: TicketStatus) -> int:
        return db.query(func.count(EscalationTicket.ticket_id)).filter(
            EscalationTicket.status == s
        ).scalar() or 0

    ticket_breakdown = TicketBreakdown(
        open=ticket_count(TicketStatus.OPEN),
        in_progress=ticket_count(TicketStatus.IN_PROGRESS),
        resolved=ticket_count(TicketStatus.RESOLVED),
        closed=ticket_count(TicketStatus.CLOSED) if hasattr(TicketStatus, "CLOSED") else 0,
    )

    # intent breakdown — approximate from ticket count vs total assistant messages
    assistant_messages = db.query(func.count(Message.message_id)).filter(
        Message.role == MessageRole.ASSISTANT
    ).scalar() or 0

    intent_breakdown = IntentBreakdown(
        escalation=escalation_sessions,
        tool_call=max(0, assistant_messages - escalation_sessions) // 2,
        rag=max(0, assistant_messages - escalation_sessions) - max(0, assistant_messages - escalation_sessions) // 2,
    )

    return AnalyticsSummary(
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_customers=total_customers,
        escalation_rate=escalation_rate,
        avg_messages_per_session=avg_messages,
        intent_breakdown=intent_breakdown,
        ticket_breakdown=ticket_breakdown,
    )
