from fastapi import APIRouter, Depends, HTTPException, Request
from ..db import get_db, Session as SessionModel, User
from ..schemas import SessionCreate, SessionResponse 
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import UUID
from ..auth.dependencies import get_current_user

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id
router = APIRouter(
    prefix="/sessions", 
    tags=["sessions"]
)


# make the session creation route 
@router.post("/", response_model=SessionResponse)
@limiter.limit("10/minute", key_func=get_user_id)
def create_session(
    request: Request,
    session: SessionCreate, 
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ): 
    new_session = SessionModel(
        user_id=session.user_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

@router.patch("/{session_id}/end", response_model=SessionResponse)
@limiter.limit("10/minute", key_func=get_user_id)
def end_session(request: Request, session_id: str, db: DBSession = Depends(get_db)): 
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    if not session: 
        raise HTTPException(status_code=404, detail=f"session with {session_id} not found")
    session.is_active = False 
    db.commit()
    db.refresh(session)
    return session