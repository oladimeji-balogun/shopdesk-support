from pinecone import Pinecone, PineconeApiKeyError, ServerlessSpec
from ..config import Config 
from .base import VectorDBClient, VectorRecord, VectorResponse
from typing import Any

class PineconeClient(VectorDBClient): 
    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)

        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if index_name not in existing_indexes: 
            self.pc.create_index(
                name=index_name, 
                metric="cosine", 
                dimension=384, 
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
        self.pc.describe_index(name=index_name)
        self.index = self.pc.Index(name=index_name)
        
        
    def upsert(self, vector_records: list[VectorRecord], namespace: str) -> None:

        try: 
            payload = [
                {
                    "id": vector_record.id, 
                    "values": vector_record.values, 
                    "metadata": vector_record.metadata
                }
                for vector_record in vector_records
            ]
            
            self.index.upsert(vectors=payload, namespace=namespace, batch_size=32, show_progress=True)
            
        except Exception as e: 
            print(f"failed to upsert vectors: {e}")
            return 

    def query(self, vector: list[float], namespace: str, filter: dict[str, Any] | None = None, top_k: int = 5) -> list[VectorResponse]:

        try: 
            resp = self.index.query(
                namespace=namespace, 
                vector=vector, 
                filter=filter, 
                include_metadata=True, 
                include_values=True, 
                top_k=top_k
            ) 
            
            vectors_response = []
            for r in resp["matches"]: 
                vectors_response.append(
                    VectorResponse(
                        id=r.id, 
                        vector=r["values"], 
                        raw_text=r["metadata"]["raw_text"], 
                        score=r["score"]
                    )
                )
            return vectors_response
        
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
            
    def query_for_strings(
        self, 
        vector: list[float], 
        namespace: str, 
        filter: dict[str, Any] | None = None, 
        top_k: int = 3
    ) -> str: 
        
        vectors_response = self.query(
            vector=vector, 
            namespace=namespace, 
            filter=filter, 
            top_k=top_k
        )
        
        return "\n\n".join(
            [
                vector.raw_text for vector in vectors_response[:3]
            ]
        )
        
    
        
    