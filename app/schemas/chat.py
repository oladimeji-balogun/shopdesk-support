from pydantic import BaseModel, Field, ConfigDict
from typing import List, Any, Literal
from datetime import datetime


# schema for creating a session
class SessionCreate(BaseModel): 
    user_id: str = Field(..., description="unique identifier of the owner of the message")

class SessionResponse(BaseModel): 
    user_id: str = Field(
        ..., 
        description="identifier of the owner of the question"
    )
    session_id: str = Field(
        ..., 
        description="to identify the session"
    )
    is_active: bool 
    created_at: datetime 
    
    model_config = ConfigDict(from_attributes=True)
    
class ChatRequest(BaseModel): 
    content: str 

class ChatResponse(BaseModel): 
    response: str 
    session_id: str 
    intent: Literal["rag", "escalate", "tool_call"] 
    
class TicketRecord(BaseModel): 
    created_at: datetime
    reason: str 
    status: str 
    ticket_id: str 
    user_id: str 
    session_id: str 
    
    model_config = ConfigDict(from_attributes=True)