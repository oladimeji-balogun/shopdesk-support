from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings): 
    DATABASE_URI: str 
    GROQ_API_KEY: str 
    PINECONE_API_KEY: str 
    EMBEDDING_MODEL: str
    PINECONE_INDEX_NAME: str
    PINECONE_NAMESPACE: str
    LOG_LEVEL: str 
    LOG_DIR: str
    
    RAG_MODEL: str 
    ROUTER_MODEL: str 
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_HOURS: int 
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str 
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True, 
        extra="ignore"
    )
    
config = Config()