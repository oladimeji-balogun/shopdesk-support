from .rag_chain import RAGChain
from .router import Router 
from ..db import User, Message, EscalationTicket, TicketStatus, MessageRole, Session as SessionModel
from langchain_groq import ChatGroq 
from ..config import config 
from sqlalchemy.orm import Session as DBSession
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
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
        db: DBSession
    ): 
        self._rag = rag 
        self._router = router 
        self._tools = tools 
        self._llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.RAG_MODEL)
        self.tools_map = {tool.name: tool for tool in tools}
        self.db = db 
        
    def _get_history(self, session_id: str) -> list[str]: 

        resp = self.db.query(Message).filter(
            Message.session_id == session_id
            ).order_by(Message.created_at.asc()).limit(
                limit=10
            )
        # if resp is None: return []
        return [
            f"User: {msg.content}" if msg.role == "user" else f"Assistant: {msg.content}" for msg in resp  
        ]
            
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
        the main method of the orchestrator
        
        it does the: 
            - taking in of the user's response
            - intent classification
            - route to the appropriate worker for the task based on the intent
            - get the result from the worker and construct messages to be saved in the database
            - save the messages in the database
            - return a nice response to the user
        """
        conversation_history = self._get_history(session_id=session_id)
        intent = self._router.route(
            query=query, 
            conversation_history=conversation_history
        )
        logger.info(f"intent classified as {intent}")
        # now do the routing 
        if intent == "rag": 
            try: 
                response = self._rag.run(query=query, conversation_history=conversation_history, namespace=config.PINECONE_NAMESPACE)
            except Exception as e: 
                logger.error(f"orchestrator rag error: {e}")
                return intent, "i am sorry, something went wrong. Please try again or contact support."
        elif intent == "tool_call": 
            try: 
                response = self._handle_tool_call(query=query, conversation_history=conversation_history, session_id=session_id)
            except Exception as e: 
                logger.error(f"orchestrator tool error: {e}")
                return intent, "i am sorry, something went wrong. Try again or contact support."

        else: 
            logger.info(f"querying the database to get the user id")
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
            logger.info("added escalation ticket to the databse")
            
            response = "I am sorry for the inconvenience, I have reported the issue to a human support agent who will be able to help you further. \nPlease hold on."
        
        # now, i want to save both messages 
        self._save_message(content=query, session_id=session_id, role=MessageRole.USER)
        self._save_message(content=response, session_id=session_id, role=MessageRole.ASSISTANT)

        return intent, response
        
          
    def _handle_tool_call(
        self, 
        query: str, 
        conversation_history: list[str], 
        session_id: str
    ): 
        llm_with_tools = self._llm.bind_tools(tools=self._tools)
        
        messages = [SystemMessage(content=TOOL_CALL_PROMPT)]
        # add the user context
        messages.append(
            SystemMessage(content=f"user_id: {self._get_user_context(session_id=session_id)}")
        )
        
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
    
    def _get_user_context(self, session_id: str) -> str: 
        session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        user = self.db.query(User).filter(
            User.user_id == session.user_id
        ).first()
        return f"name: {user.name}, email: {user.email}, phone-no: {user.phone}, user_id: {user.user_id}"