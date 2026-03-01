from .rag_chain import RAGChain
from .router import Router 
from ..db import User, Message, SessionLocal
from ..tools import get_account_info, get_order_status, get_recent_orders
from langchain_groq import ChatGroq 
from ..config import config 

class Orchestrator: 
    def __init__(
        self,
        rag: RAGChain, 
        router: Router,
        tools: list
    ): 
        self._rag = rag 
        self._router = router 
        self._tools = tools 
        self._llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.RAG_MODEL)
        self.tool_map = {tool.name: tool for tool in tools}
        
    def _get_history(self, session_id: str) -> list[str]: 
        db = SessionLocal()
        
        try: 
            resp = db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at.asc()).limit(
                limit=10
            )
            # if resp is None: return []
            return [
                f"User: {msg.content}" if msg.role == "user" else f"Assistant: {msg.content}" for msg in resp  
            ]
        finally: 
            db.close()
            
    def _save_message(self, content: str, session_id: str, role: str): 
        db = SessionLocal()
        payload = Message(
            session_id=session_id, 
            role=role, 
            content=content
        )
        try: 
            db.add(payload)
            db.commit()
        finally: 
            db.close()