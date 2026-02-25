import hashlib 

def make_vector_id(text: str): 
    id = hashlib.sha256(text.encode()).hexdigest()
    return id 