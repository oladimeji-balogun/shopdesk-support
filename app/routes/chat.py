from fastapi import APIRouter, Depends
from ..db import get_db, Message, Session as SessionModel 
from ..schemas import ChatRequest, ChatResponse
from sqlalchemy.orm import Session as DBSession 
from ..dependencies import get_orchestrator
from ..agent import Orchestrator


router = APIRouter(
    prefix="/chat", 
    tags=["chat"]
)


@router.post("/{session_id}", response_model=ChatResponse)
def send_message(
    session_id: str, 
    request: ChatRequest, 
    orchestrator: Orchestrator = Depends(get_orchestrator)
): 
    intent, response = orchestrator.handle(query=request.content, session_id=session_id)
    
    return ChatResponse(
        response=response, 
        session_id=session_id, 
        intent=intent
    )