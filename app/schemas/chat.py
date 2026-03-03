from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID


# schema for creating a session
class SessionCreate(BaseModel): 
    user_id: UUID = Field(..., description="unique identifier of the owner of the message")

class SessionResponse(BaseModel): 
    user_id: UUID = Field(
        ..., 
        description="identifier of the owner of the question"
    )
    session_id: UUID = Field(
        ..., 
        description="to identify the session"
    )
    is_active: Optional[bool]
    created_at: datetime 
    
    model_config = ConfigDict(from_attributes=True)
    
class ChatRequest(BaseModel): 
    content: str 

class ChatResponse(BaseModel): 
    response: str 
    session_id: UUID 
    intent: Literal["rag", "escalate", "tool_call"] 
    
class TicketRecord(BaseModel): 
    created_at: datetime
    reason: str 
    status: str 
    ticket_id: UUID 
    user_id: UUID 
    session_id: UUID 
    
    model_config = ConfigDict(from_attributes=True)