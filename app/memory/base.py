"""
memory/base.py - an abstract base class for construction different types of memory objects
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

class MemoryRecord(BaseModel): 
    id: str = Field(..., description="a unique identifier for each memory record")
    content: str = Field(..., description="the memory content")

class MemoryBase(ABC): 
    @abstractmethod
    def add(self, record: MemoryRecord): 
        ...
        
    @abstractmethod
    def trim_memory(self): 
        ... 
        
    @abstractmethod
    def get_context_str() -> str: 
        ... 
        
    
    @abstractmethod
    def clear(self): 
        ...
        
    
         