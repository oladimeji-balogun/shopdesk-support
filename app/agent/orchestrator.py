from .rag_chain import RAGChain
from .router import Router 
from ..db import User, Message, SessionLocal
from ..tools import get_account_info, get_order_status, get_recent_orders
from langchain_groq import ChatGroq 
from ..config import config 
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from ..utils import load_prompt

TOOL_CALL_PROMPT = load_prompt(filename="tool-call")
ORCHESTRATOR_PROMPT = load_prompt(filename="orchestrator")

class Orchestrator: 
    def __init__(
        self,
        rag: RAGChain, 
        router: Router,
        tools: list[BaseTool], 
        db: Session
    ): 
        self._rag = rag 
        self._router = router 
        self._tools = tools 
        self._llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.RAG_MODEL)
        self.tools_map = {tool.name: tool for tool in tools}
        self.db = db 
        
    def _get_history(self, session_id: str) -> list[str]: 

        try: 
            resp = self.db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.asc()).limit(
                limit=10
            )
            # if resp is None: return []
            return [
                f"User: {msg.content}" if msg.role == "user" else f"Assistant: {msg.content}" for msg in resp  
            ]
        finally: 
            self.db.close()
            
    def _save_message(self, content: str, session_id: str, role: str): 
        payload = Message(
            session_id=session_id, 
            role=role, 
            content=content
        )
        try: 
            self.db.add(payload)
            self.db.commit()
        finally: 
            self.db.close()
            
    def _handle_tool_call(
        self, 
        query: str, 
        conversation_history: list[str]
    ): 
        llm_with_tools = self._llm.bind_tools(tools=self._tools)
        messages = [SystemMessage(content=TOOL_CALL_PROMPT)]
        
        history = [
            HumanMessage(content=s.replace("User: ", "")) if s.startswith("User: ") else AIMessage(content=s.replace("Assistant: ", "")) for s in conversation_history
        ]
        
        messages += history
        messages.append(HumanMessage(content=query))
        # prompt = ChatPromptTemplate.from_messages(
        #     [
        #         ("system", TOOL_CALL_PROMPT), 
        #         MessagesPlaceholder(variable_name="history"), 
        #         HumanMessage(content=query)
        #     ]
        # )
        
        response = llm_with_tools.invoke(messages)
        
        messages.append(response)
        
        # handling the edge-case of no tool call 
        if not response.tool_calls: 
            return response.content
        # now let's handle the tool call 
        for tool_call in response.tool_calls: 
            tool = self.tools_map[tool_call["name"]]
            result = tool.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    content=str(result), 
                    tool_call_id=tool_call["id"]
                )
            )
        
        # now passing the the updated history back to the final llm 
        final_response = self._llm.invoke(messages)
        return final_response.content