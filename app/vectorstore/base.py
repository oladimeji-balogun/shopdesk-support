from abc import ABC, abstractmethod 
from pydantic import BaseModel, Field 
from typing import Any


# the data model for each entry in the vector db 
class VectorRecord(BaseModel): 
    id: str = Field(..., description="a unique identifier of each vector in the daatabase")
    values: list[float] = Field(..., description="the vector object for each chunk")
    metadata: dict[str, Any]
    
# model for pinecone response
class VectorResponse(BaseModel):
    id: str
    vector: list[float]
    raw_text: str 
    score: float 
    
    
class VectorDBClient(ABC): 
    @abstractmethod
    def upsert(self, vectors: list[VectorRecord], namespace: str): 
        ... 
    
    @abstractmethod
    def query(self, text: str, namespace: str): 
        ...
    
    @abstractmethod  
    def delete(self, ids: list[str], namespace: str): 
        ... 
        
    