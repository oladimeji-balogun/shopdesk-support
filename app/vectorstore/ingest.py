"""
vectorstore/ingest.py - handles the entire processing of the documents from the knowledge base 

functions: 
    - load the contents of the documents 
    - process them into chunks 
    - process the chunks into embeddings
    - upload the chunks into pinecone
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter 
from fastembed import TextEmbedding
from ..config import config 
from ..utils.vector_id import make_vector_id 
from .pinecone_client import PineconeClient, VectorRecord

from ..utils.logger import setup_logger 

logger = setup_logger(
    name="ingest", 
    verbose=True
)

class DocumentFactory: 
    def __init__(self, embedding_model: TextEmbedding, pc_client: PineconeClient): 
        self.embedding_model = embedding_model 
        self.pc_client = pc_client

    def load_document(self, filepath: str) -> str: 
        logger.info("loading the contents of the knowledgebase")
        try: 
            with open(filepath, "r") as f: 
                content = f.read()
            return content.strip()
        except FileNotFoundError: 
            print(f"file not found")
            return 
        except Exception as e: 
            print(f"load operation failed: {e}")
            return 
        
    def chunk_text(self, text: str) -> list[str]: 
        logger.info("creating semantic chunks")
        chunker = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        chunks = chunker.split_text(text=text)
        return chunks 
    
    def embed_chunks(self, chunks: list[str]) -> list[list[float]]: 
        logger.info("creating embeddings from chunks")
        embeddings = list(self.embedding_model.embed(documents=chunks, batch_size=32))
        return [e.tolist() for e in embeddings]
    
    def embed_query(self, query: str) -> list[float]: 
        embeddings = list(self.embedding_model.embed(documents=[query]))
        return embeddings[0].tolist()
    
    
    
    def upload_to_pinecone(self, chunks: list[str], namespace: str): 
        logger.info("uploading vectors to pinecone")
        embeddings = self.embed_chunks(chunks=chunks)
        vector_records = [
            VectorRecord(
                id=make_vector_id(text=chunk), 
                values=embeddings[i], 
                metadata={"raw_text": chunk}
            ) for i, chunk in enumerate(chunks)
        ]
        
        
            
        # upload to pinecone
        self.pc_client.upsert(vector_records=vector_records, namespace=namespace)
        logger.info("uploaded all embeddings to pinecone")
        


def run_ingestion(): 
    embedding_model = TextEmbedding(model_name=config.EMBEDDING_MODEL)
    logger.info("preparing the document factory")
    factory = DocumentFactory(
        embedding_model=embedding_model, 
        pc_client=PineconeClient(
            api_key=config.PINECONE_API_KEY, 
            index_name=config.PINECONE_INDEX_NAME
        )
    )
    # logger.info("loading the documentss")
    
    # text_content = factory.load_document(filepath="./knowledge-base/faqs.md")
    # chunks = factory.chunk_text(text=text_content)
    # # load docs to pinecone
    # factory.upload_to_pinecone(chunks=chunks, namespace=config.PINECONE_NAMESPACE)
    
    
    sample_text = "tell me about shopdesk?"
    vector = factory.embed_query(query=sample_text)
    print(f"embedded vector: \n{vector}")
if __name__ == "__main__": 
    run_ingestion()