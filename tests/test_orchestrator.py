from app.agent import Orchestrator 
from unittest.mock import MagicMock 
import pytest 

class TestOrchestrator: 
    @pytest.fixture
    def orchestrator(self): 
        
        rag_mock = MagicMock()
        rag_mock.run.return_value = "this is the return policy..."
        
        router_mock = MagicMock()
        router_mock.route.return_value = "rag"

        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value = []
        orch = Orchestrator(
            rag=rag_mock, 
            router=router_mock, 
            tools=[], 
            db=db_mock
        )
        return orch
    
    def test_handle(self, orchestrator): 
        sample_text = "what is the return policy at ShopDesk?"
        result = orchestrator.handle(
            query=sample_text, 
            session_id="929idsdskjf"
        ) 
        
        assert isinstance(result, str)
        
    def test_handle_tool_call(self, orchestrator): 
        sample_text = "what is the status of order 4540"
        result = orchestrator._handle_tool_call(
            query=sample_text, 
            conversation_history=[]
        ) 
        assert isinstance(result, str)
        
    def test_save_message(self, orchestrator): 
        result = orchestrator._save_message(
            content="i am just testing", 
            session_id="9ikakggjkj", 
            role="user"
        ) 
        orchestrator.db.add.assert_called_once()    
        orchestrator.db.commit.assert_called_once()
            
    def test_get_history(self, orchestrator): 
        history = orchestrator._get_history(
            session_id="heakhia9e"
        ) 
        
        assert isinstance(history, list)