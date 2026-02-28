from pydantic import BaseModel 
from typing import Literal 

class RouterIntent(BaseModel): 
    intent: Literal["rag", "tool_call", "escalate"]

