def test_chunk_text(fake_document_factory): 
    factory = fake_document_factory
    chunks = factory.chunk_text(text="tokens and" * 700)
    assert len(chunks) > 0
    
def test_load_document(fake_document_factory): 
    factory = fake_document_factory
    text = factory.load_document(filepath="./knowledge-base/faqs.md")
    assert len(text) > 0
 