from ..vectorstore import DocumentFactory, PineconeClient 
from ..config import config 
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder 
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from ..utils.load_prompt import load_prompt 

RAG_SYSTEM_PROPMT = load_prompt(filename="rag")


class RAGChain: 
    def __init__(
        self, 
        document_factory: DocumentFactory, 
        pinecone_client: PineconeClient
    ): 
        self.document_factory = document_factory
        self.pinecone_client = pinecone_client
        self._llm = ChatGroq(api_key=config.GROQ_API_KEY, model=config.RAG_MODEL)
        
    def run(self, query: str, conversation_history: list[BaseMessage], namespace: str): 
        query_embeddings = self.document_factory.embed_query(query=query)
        
        # Bug 2.8: Use score threshold to prevent hallucinations
        vectors_response = self.pinecone_client.query(
            vector=query_embeddings, 
            namespace=namespace,
            top_k=3
        )
        
        # Filter by score (similarity threshold)
        relevant_chunks = [v.raw_text for v in vectors_response if v.score >= 0.70]
        
        if not relevant_chunks:
            retrieved_text = "No relevant information found in the knowledge base."
        else:
            retrieved_text = "\n\n".join(relevant_chunks)
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROPMT), 
                MessagesPlaceholder(variable_name="history"), 
                ("human", f"Question: {query}\n\nContext: {retrieved_text}")
            ]
        )
        
        rag_chain = prompt | self._llm
        response = rag_chain.invoke({"history": conversation_history})
        return response.content