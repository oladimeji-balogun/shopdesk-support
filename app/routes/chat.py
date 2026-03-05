from fastapi import APIRouter, Depends, Request
from ..db import get_db, Message, Session as SessionModel, User
from ..schemas import ChatRequest, ChatResponse
from sqlalchemy.orm import Session as DBSession 
from ..dependencies import get_orchestrator
from ..agent import Orchestrator

from ..auth.dependencies import get_current_user

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id

router = APIRouter(
    prefix="/chat", 
    tags=["chat"]
)


@router.post("/{session_id}", response_model=ChatResponse)
@limiter.limit("120/minute", key_func=get_user_id)
def send_message(
    request: Request,
    session_id: str, 
    chat_request: ChatRequest, 
    orchestrator: Orchestrator = Depends(get_orchestrator),
    current_user: User = Depends(get_current_user)
): 
    intent, response = orchestrator.handle(query=chat_request.content, session_id=session_id)
    
    return ChatResponse(
        response=response, 
        session_id=session_id, 
        intent=intent
    )