"""
vectorstore/ingest.py - handles the entire processing of the documents from the knowledge base 

functions: 
    - load the contents of the documents 
    - process them into chunks 
    - process the chunks into embeddings
    - upload the chunks into pinecone
"""

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from sentence_transformers import SentenceTransformer

from .pinecone_client import PineconeClient, VectorRecord, VectorResponse
from ..config import Config, config 
from ..utils import make_vector_id 

class DocumentFactory: 
    def __init__(self, embedding_model: str, pc_client: PineconeClient): 
        self.embedding_model = SentenceTransformer(embedding_model)
        self.pc_client = pc_client

    def load_document(self, filepath: str) -> str: 
        
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
        chunker = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        chunks = chunker.split_text(text=text)
        return chunks 
    
    def embed_chunks(self, chunks: list[str]) -> list[list[float]]: 
        embeddings = self.embedding_model.encode(sentences=chunks, batch_size=32)
        return embeddings
    
    def embed_query(self, query: str) -> list[float]: 
        embeddings = self.embedding_model.encode(query)
        return embeddings
    
    
    
    def upload_to_pinecone(self, chunks: list[str], namespace: str): 
        embeddings = self.embed_chunks(chunks=chunks)
        vector_records = [
            VectorRecord(
                id=make_vector_id(text=chunk), 
                values=embeddings[i].tolist(), 
                metadata={"raw_text": chunk}
            ) for i, chunk in enumerate(chunks)
        ]
        
        
            
        # upload to pinecone
        self.pc_client.upsert(vector_records=vector_records, namespace=namespace)
        


def run_ingestion(): 
    print("preparing the document factory")
    factory = DocumentFactory(
        embedding_model=config.EMBEDDING_MODEL, 
        pc_client=PineconeClient(
            api_key=config.PINECONE_API_KEY, 
            index_name=config.PINECONE_INDEX_NAME
        )
    )
    print("loading the documentss")
    
    text_content = factory.load_document(filepath="./knowledge-base/faqs.md")
    print("converting the loaded documents into chunks")
    chunks = factory.chunk_text(text=text_content)
    print(f"length of chunks: {len(chunks)}")
    # load docs to pinecone
    print("uploading chunks to pinecone")
    factory.upload_to_pinecone(chunks=chunks, namespace=config.PINECONE_NAMESPACE)
    print("uploaded all documents successfully")
    
if __name__ == "__main__": 
    run_ingestion()