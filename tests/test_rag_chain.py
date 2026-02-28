from app.agent import RAGChain
from unittest.mock import MagicMock 
import pytest
from app.config import config

class TestRagChain: 
    # create the rag chain fixture 
    @pytest.fixture
    def rag_chain(self): 
        chain = RAGChain(
            document_factory=MagicMock(), 
            pinecone_client=MagicMock(), 
        )
        
        return chain 
    
    def test_run(self, rag_chain): 
        question = "hello, how are you doing today?"
        answer = rag_chain.run(query=question, namespace=config.PINECONE_NAMESPACE, conversation_history=[])
        assert answer is not None
        assert isinstance(answer, str)