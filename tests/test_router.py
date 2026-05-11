from app.agent import Router 
from unittest.mock import MagicMock 
import pytest 
from langchain_core.messages import HumanMessage


class TestRouter: 
    # make the fixture 
    @pytest.fixture 
    def router(self): 
        # Router.__init__ takes no arguments now
        router = Router()
        router.llm = MagicMock()
        return router 
        return router

    # test the route method
    def test_route(self, router):
        question = "hello, i want to know the status of order #894"

        # Mock structured output
        # In LangChain pipes, invoking the chain invokes the last step.
        mock_structured_llm = MagicMock()
        mock_decision = MagicMock()
        mock_decision.intent = "tool_call"
        mock_structured_llm.invoke.return_value = mock_decision

        router.llm.with_structured_output.return_value = mock_structured_llm

        decision = router.route(query=question, conversation_history=[HumanMessage(content="hello")])
        assert decision == "tool_call"