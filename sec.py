import secrets 

sample_key = secrets.token_urlsafe(nbytes=64)
print(sample_key)