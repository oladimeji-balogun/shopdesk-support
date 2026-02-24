from pinecone import Pinecone, PineconeApiKeyError
from ..config import Config 
from .base import VectorDBClient, VectorRecord, VectorResponse
from typing import Any

class PineconeClient(VectorDBClient): 
    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)

        if not self.pc.has_index(index_name): 
            self.index = self.pc.Index(
                name=index_name, 
                cloud="aws", 
                region="us-east-1"
            )
    def upsert(self, vectors: list[VectorRecord], namespace: str) -> None:

        try: 
            self.index.upsert(
                vectors=vectors, 
                batch_size=32, 
                show_progress=True, 
                namespace=namespace
            )
        except Exception as e: 
            print(f"failed to upsert vectors: {e}")

    def query(self, vector: list[float], namespace: str, filter: dict[str, Any], top_k: int) -> list[VectorResponse]:

        try: 
            resp = self.index.query(
                namespace=namespace, 
                vector=vector, 
                filter=filter, 
                include_metadata=True, 
                include_values=True, 
                top_k=top_k
            ) 
            
            vector_records = []
            for r in resp["matches"]: 
                vector_records.append(
                    VectorResponse(
                        id=r.id, 
                        vector=r["values"], 
                        raw_text=r["metadata"]["raw_text"], 
                        score=r["score"]
                    )
                )
            return vector_records
        except Exception as e: 
            print(f"failed to query database: {e}")
            return 
        
    def delete(self, ids: list[str], namespace: str): 
        try: 
            self.index.delete(
                ids=ids, 
                namespace=namespace
            )
        except Exception as e: 
            print(f"failed to delete vectors: {e}")
        
        
    
        
    