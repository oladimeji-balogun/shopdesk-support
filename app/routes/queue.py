from fastapi import APIRouter, Depends, Request
from ..schemas import TicketRecord 
from ..db import EscalationTicket, get_db, TicketStatus
from sqlalchemy.orm import Session as DBSession

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
    db: DBSession = Depends(get_db)
): 
    
    open_tickets = db.query(EscalationTicket).filter(
        EscalationTicket.status == TicketStatus.OPEN
    ).all()
    return open_tickets