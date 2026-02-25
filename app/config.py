from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings): 
    DATABASE_URI: str 
    GROQ_API_KEY: str 
    PINECONE_API_KEY: str 
    EMBEDDING_MODEL: str
    PINECONE_INDEX_NAME: str
    PINECONE_NAMESPACE: str
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True, 
        extra="ignore"
    )
    
config = Config()