from .agent import Orchestrator, RAGChain, Router 
from .vectorstore import DocumentFactory, PineconeClient 
from .db import get_db 
from fastapi import Depends 
from sqlalchemy.orm import Session as DBSession 
from fastembed import TextEmbedding
from .config import config 
from .tools import get_account_info, get_order_status, get_recent_orders
from langchain_groq import ChatGroq


embedding_model = TextEmbedding(model_name=config.EMBEDDING_MODEL)
pinecone_client = PineconeClient(
    api_key=config.PINECONE_API_KEY, 
    index_name=config.PINECONE_INDEX_NAME
)

document_factory = DocumentFactory(
    embedding_model=embedding_model, 
    pc_client=pinecone_client
)

rag = RAGChain(
    document_factory=document_factory, 
    pinecone_client=pinecone_client
)

router = Router()

# Bug 2.5: Singleton LLM client to be shared across requests
llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.RAG_MODEL)

def get_orchestrator(
    db: DBSession = Depends(get_db)
) -> Orchestrator: 
    orchestrator = Orchestrator(
        rag=rag, 
        router=router, 
        db=db, 
        tools=[get_recent_orders, get_order_status, get_account_info],
        llm=llm
    )
    return orchestrator 
