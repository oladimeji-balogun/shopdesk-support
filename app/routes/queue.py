from fastapi import APIRouter, Depends, Request
from ..schemas import TicketRecord 
from ..db import EscalationTicket, get_db, TicketStatus, User
from sqlalchemy.orm import Session as DBSession
from ..auth.dependencies import get_current_user

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id

router = APIRouter(
    prefix="/queue", 
    tags=["queue"]
)

@router.get("/", response_model=list[TicketRecord])
@limiter.limit("5/minute", key_func=get_user_id)
def get_open_tickets(
    request: Request,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    
    open_tickets = db.query(EscalationTicket).filter(
        EscalationTicket.status == TicketStatus.OPEN
    ).all()
    return open_tickets