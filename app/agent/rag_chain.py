from ..vectorstore import DocumentFactory, PineconeClient 
from ..config import config 
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder 
from langchain_core.messages import AIMessage, HumanMessage

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
        
    def run(self, query, conversation_history: list[str], namespace: str): 
        query_embeddings = self.document_factory.embed_query(query=query)
        # use the embeddings to query the vector db
        retrieved_text = self.pinecone_client.query_for_strings(vector=query_embeddings, namespace=namespace)
        
        history = [
            HumanMessage(content=message.replace("User", "")) if message.startswith("User") else AIMessage(content=message.replace("Assistant", "")) for message in conversation_history
        ]
        
        # create an instance of the memory object 
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROPMT), 
                MessagesPlaceholder(variable_name="history"), 
                ("human", f"Question: {query}\n\nContext: {retrieved_text}")
            ]
        )
        
        rag_chain = prompt | self._llm
        response = rag_chain.invoke({"history": history})
        return response.content

        
        