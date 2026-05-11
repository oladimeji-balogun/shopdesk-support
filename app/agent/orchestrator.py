from .rag_chain import RAGChain
from .router import Router
from ..db import User, Message, EscalationTicket, TicketStatus, MessageRole, Session as SessionModel
from langchain_groq import ChatGroq
from ..config import config
from sqlalchemy.orm import Session as DBSession
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import BaseTool

from ..utils import load_prompt
from ..utils import setup_logger

logger = setup_logger(name="orchestrator", verbose=True)
TOOL_CALL_PROMPT = load_prompt(filename="tool-call")


class Orchestrator:
    def __init__(
        self,
        rag: RAGChain,
        router: Router,
        tools: list[BaseTool],
        db: DBSession,
        llm: ChatGroq,
    ):
        self._rag = rag
        self._router = router
        self._tools = tools
        self._llm = llm  # Bug 2.5: injected singleton, not created per-request
        self.tools_map = {tool.name: tool for tool in tools}
        self.db = db

    def _get_history(self, session_id: str) -> list[BaseMessage]:
        """
        Returns the last 10 messages as typed LangChain message objects.
        Bug 2.3 fix: uses MessageRole enum instead of string prefix stripping.
        """
        messages = self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).limit(10).all()

        history: list[BaseMessage] = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))
        return history

    def _save_message(self, content: str, session_id: str, role: str):
        payload = Message(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(payload)
        self.db.commit()

    def handle(
        self,
        query: str,
        session_id: str
    ):
        """
        Main orchestration method:
        - classifies intent via router
        - routes to RAG, tool call, or escalation worker
        - saves both user and assistant messages
        - returns (intent, response)
        """
        conversation_history = self._get_history(session_id=session_id)
        intent = self._router.route(
            query=query,
            conversation_history=conversation_history
        )
        logger.info(f"intent classified as {intent}")

        if intent == "rag":
            try:
                response = self._rag.run(
                    query=query,
                    conversation_history=conversation_history,
                    namespace=config.PINECONE_NAMESPACE
                )
            except Exception as e:
                logger.error(f"orchestrator rag error: {e}")
                return intent, "I am sorry, something went wrong. Please try again or contact support."

        elif intent == "tool_call":
            try:
                response = self._handle_tool_call(
                    query=query,
                    conversation_history=conversation_history,
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"orchestrator tool error: {e}")
                return intent, "I am sorry, something went wrong. Try again or contact support."

        else:
            logger.info("querying the database to get the user id")
            session = self.db.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()
            user_id = session.user_id

            ticket = EscalationTicket(
                session_id=session_id,
                reason=query,
                user_id=user_id,
                status=TicketStatus.OPEN
            )
            self.db.add(ticket)
            self.db.commit()
            logger.info("added escalation ticket to the database")

            response = (
                "I am sorry for the inconvenience. I have reported the issue to a human support agent "
                "who will be able to help you further.\nPlease hold on."
            )

        # save both messages
        self._save_message(content=query, session_id=session_id, role=MessageRole.USER)
        self._save_message(content=response, session_id=session_id, role=MessageRole.ASSISTANT)

        return intent, response

    def _handle_tool_call(
        self,
        query: str,
        conversation_history: list[BaseMessage],
        session_id: str
    ):
        llm_with_tools = self._llm.bind_tools(tools=self._tools)

        messages = [SystemMessage(content=TOOL_CALL_PROMPT)]

        # Bug 2.2 fix: send only user_id to the LLM — no PII (email, phone, name)
        user_id = self._get_user_id(session_id=session_id)
        messages.append(SystemMessage(content=f"user_id: {user_id}"))

        # Bug 2.3 fix: history is already typed message objects — no string parsing needed
        messages += conversation_history
        messages.append(HumanMessage(content=query))

        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # edge case: no tool call triggered — return LLM's direct response
        if not response.tool_calls:
            return response.content

        # execute each tool call
        for tool_call in response.tool_calls:
            tool = self.tools_map[tool_call["name"]]
            result = tool.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )

        # pass updated history back to LLM for a final, human-readable response
        final_response = self._llm.invoke(messages)
        return final_response.content

    def _get_user_id(self, session_id: str) -> str:
        """
        Bug 2.2: Returns only the user_id — strips all PII (name, email, phone)
        that was previously sent raw to the external LLM.
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        if not session:
             return "unknown"
        return str(session.user_id)