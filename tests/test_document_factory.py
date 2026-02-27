def test_chunk_text(fake_document_factory): 
    factory = fake_document_factory
    chunks = factory.chunk_text(text="tokens and" * 700)
    assert len(chunks) > 0
    assert all(len(chunk) <= 500 for chunk in chunks)
    
def test_load_document(fake_document_factory): 
    factory = fake_document_factory
    text = factory.load_document(filepath="api/faqs.md")
    assert text is None 
 
 
def test_embedding_size_respected(fake_document_factory): 
    factory = fake_document_factory 
    text = "how are you there? " * 15
    embeddings = factory.embed_chunks(chunks=[text])
    assert len(embeddings[0]) == 384