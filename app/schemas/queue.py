from pydantic import BaseModel 
from ..db import TicketStatus

class TicketUpdate(BaseModel): 
    status: TicketStatus 