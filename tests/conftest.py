from unittest.mock import MagicMock, patch 
import pytest 
from app.vectorstore import DocumentFactory

# creating a mock fixture for the document factor class
@pytest.fixture
def fake_document_factory(): 
    fake_pinecone_client = MagicMock()
    fake_embedding_model = MagicMock()

    factory = DocumentFactory(
        embedding_model=fake_embedding_model, 
        pc_client=fake_pinecone_client
    )
    
    return factory