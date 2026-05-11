from fastapi import APIRouter, Depends, HTTPException, Request
from ..db import get_db, Session as SessionModel, User, Message
from ..schemas import SessionCreate, SessionResponse 
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import UUID
from ..auth.dependencies import get_current_user
from pydantic import BaseModel, Field
from typing import Optional

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id
router = APIRouter(
    prefix="/sessions", 
    tags=["sessions"]
)


# create a session
@router.post("/", response_model=SessionResponse)
@limiter.limit("10/minute", key_func=get_user_id)
def create_session(
    request: Request,
    # session: SessionCreate, 
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ): 
    new_session = SessionModel(
        user_id=current_user.user_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session


# end a sesstion
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

# get all messages associated with a sesionss
@router.get("/{session_id}/messages")
def get_messages(
    session_id: str, 
    db: DBSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
): 
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).all()

    return messages

# get all user sessions 
@router.get("/")
def get_all_sessions(
    current_user: User = Depends(get_current_user), 
    db: DBSession = Depends(get_db)
): 
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.user_id,
        SessionModel.is_active == True
    ).order_by(SessionModel.created_at.desc()).all()

    return sessions


# hard delete a session and all its messages
@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id,
        SessionModel.user_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    # messages cascade-delete via FK ondelete="CASCADE"
    db.delete(session)
    db.commit()


class RatingPayload(BaseModel):
    rating: int = Field(..., ge=1, le=5)


@router.post("/{session_id}/rate")
def rate_session(
    session_id: str,
    payload: RatingPayload,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id,
        SessionModel.user_id == current_user.user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    session.rating = payload.rating
    db.commit()
    return {"message": "rating saved", "rating": payload.rating}