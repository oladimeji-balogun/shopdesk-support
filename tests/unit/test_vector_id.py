from app.utils.vector_id import make_vector_id

def test_vector_id(): 
    # check the determinism of the id generation function
    text = "black-black-black-sheep"
    first_id = make_vector_id(text=text)
    second_id = make_vector_id(text=text)
    assert first_id == second_id