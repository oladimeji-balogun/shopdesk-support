from abc import ABC, abstractmethod 
from pydantic import BaseModel, Field 
from typing import Any


# the data model for each entry in the vector db 
class VectorRecord(BaseModel): 
    id: str = Field(..., description="a unique identifier of each vector in the daatabase")
    vector: list[float] = Field(..., description="the vector object for each chunk")
    metadata: dict[str, Any]
    
# model for pinecone response
class VectorResponse(BaseModel):
    vector: list[float]
    raw_text: str 
    
    
class VectorDBClient(ABC): 
    @abstractmethod
    def upsert(vectors: list[VectorRecord], namespace: str): 
        ... 
    
    @abstractmethod
    def query(text: str, namespace: str): 
        ...
    
    @abstractmethod  
    def delete(ids: list[str], namespace: str): 
        ... 
        
    