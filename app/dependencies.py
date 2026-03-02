from .agent import Orchestrator, RAGChain, Router 
from .vectorstore import DocumentFactory, PineconeClient 
from .db import get_db 
from fastapi import Depends 
from sqlalchemy.orm import Session as DBSession 
from sentence_transformers import SentenceTransformer
from .config import config 
from .tools import get_account_info, get_order_status, get_recent_orders


embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
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

def get_orchestrator(
    
) -> Orchestrator: 
    orchestrator = Orchestrator(
        rag=rag, 
        router=router, 
        db=Depends(get_db), 
        tools=[get_recent_orders, get_order_status, get_account_info]
    )
    return orchestrator 

