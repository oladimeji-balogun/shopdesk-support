from pydantic import BaseModel 
from typing import Literal 
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ..utils import load_prompt
from langchain_groq import ChatGroq
from ..config import config

class RouterDecision(BaseModel): 
    intent: Literal["rag", "tool_call", "escalate"]

ROUTER_SYSTEM_PROMPT = load_prompt(filename="router")
class Router: 
    
    def __init__(
        self
    ): 
        self.llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.ROUTER_MODEL)
        
    # the route method 
    def route(self, query: str, conversation_history: list[str]) -> str: 
        """
        takes the user and return the intent of the user
        this intent is what would be used to determine whether the agent shoud: 
            - use tools or, 
            - use rag, 
            - escalate the issue
        
        """
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ROUTER_SYSTEM_PROMPT), 
                MessagesPlaceholder(variable_name="history"), 
                ("human", query)
            ]
        )
        
        history = [
            HumanMessage(content=s.replace("User: ", "")) if s.startswith("User: ") else AIMessage(content=s.replace("Assistant: ", "")) for s in conversation_history
            ]
        
        structured_llm = self.llm.with_structured_output(schema=RouterDecision)
        
        router = prompt | structured_llm

        response = router.invoke({"history": history})
        return response.intent
        
