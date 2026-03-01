from app.agent import Router 
from unittest.mock import MagicMock 
import pytest 


class TestRouter: 
    # make the fixture 
    @pytest.fixture 
    def router(self): 
        router = Router(
            document_factory=MagicMock(), 
            pinecone_client=MagicMock()
        )
        
        return router 
    
    # test the route method 
    def test_route(self, router): 
        question = "User: hello, i want to know the status of order #894"
        decision = router.route(query=question, conversation_history=["hello"])
        assert decision in ["rag", "escalate", "tool_call"]

        