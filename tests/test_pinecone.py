from unittest.mock import MagicMock 
import pytest 

from app.vectorstore import PineconeClient 
from app.config import config
from app.vectorstore.base import VectorRecord, VectorResponse
from app.utils.vector_id import make_vector_id
import random

class TestPineconeClient: 
    # fixture of the pinecone client
    @pytest.fixture 
    def pc_client(self): 
        pc = PineconeClient(api_key=config.PINECONE_API_KEY, index_name=config.PINECONE_INDEX_NAME)
        return pc 
    
    def test_upsert(self, pc_client): 
        vector_records = [
            VectorRecord(
                id=make_vector_id(text=f"id_{i}"), 
                values=[random.random() for i in range(384)], 
                metadata={"raw_text": "i am just testing."}
            ) for i in range(3)
        ]
        
        # make the uploads 
        pc_client.upsert(vector_records, "namespace for running tests")
    
    def test_query(self, pc_client): 
        query_embedding = [random.random() for i in range(384)]
        results = pc_client.query(vector=query_embedding, namespace=config.PINECONE_NAMESPACE)
        assert len(results) == 5 
        assert all(isinstance(result, VectorResponse) for result in results)
        assert all(len(result.vector) == 384 for result in results)
    