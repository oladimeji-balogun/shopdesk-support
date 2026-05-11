from app.agent import Orchestrator 
from unittest.mock import MagicMock 
import pytest 
from langchain_core.messages import HumanMessage, AIMessage

class TestOrchestrator: 
    @pytest.fixture
    def orchestrator(self): 
        
        rag_mock = MagicMock()
        rag_mock.run.return_value = "this is the return policy..."
        
        router_mock = MagicMock()
        router_mock.route.return_value = "rag"

        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        llm_mock = MagicMock()
        
        orch = Orchestrator(
            rag=rag_mock, 
            router=router_mock, 
            tools=[], 
            db=db_mock,
            llm=llm_mock
        )
        return orch
    
    def test_handle(self, orchestrator): 
        sample_text = "what is the return policy at ShopDesk?"
        intent, response = orchestrator.handle(
            query=sample_text, 
            session_id="929idsdskjf"
        ) 
        
        assert isinstance(response, str)
        assert intent == "rag"
        
    def test_handle_tool_call(self, orchestrator): 
        sample_text = "what is the status of order 4540"
        orchestrator._llm.bind_tools.return_value.invoke.return_value.content = "Order is shipped"
        orchestrator._llm.bind_tools.return_value.invoke.return_value.tool_calls = []
        
        result = orchestrator._handle_tool_call(
            query=sample_text, 
            conversation_history=[],
            session_id="session-123"
        ) 
        assert isinstance(result, str)
        
    def test_save_message(self, orchestrator): 
        orchestrator._save_message(
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