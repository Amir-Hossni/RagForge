from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    
    APP_NAME : str
    APP_VERSION : str

    FILE_ALLOWED_TYPES : list[str]
    FILE_MAX_SIZE : int
    FILE_DEFAULT_CHUNK_SIZE : int
    
    MONGODB_URI : str
    MONGODB_DATABASE : str
    
    #LLM PROVIDERS     
    GENERATION_BACKEND : Optional[str] = None
    EMBEDDING_BACKEND : Optional[str] = None

    OPENAI_API_KEY : Optional[str] = None
    OPENAI_API_URL : Optional[str] = None

    COHERE_API_KEY : Optional[str] = None
    
    ANTHROPIC_API_KEY : Optional[str] = None
    GOOGLE_API_KEY : Optional[str] = None
    
    NVIDIA_API_KEY : Optional[str] = None
    NVIDIA_API_URL : str = "https://integrate.api.nvidia.com/v1"
    
    OLLAMA_API_URL : str = "http://localhost:11434"

    GENERATION_MODEL_ID : Optional[str] = None
    EMBEDDING_MODEL_ID : Optional[str] = None
    EMBEDDING_MODEL_SIZE : Optional[int] = None

    INPUT_DEFAULT_MAX_CHARACTERS : Optional[int] = None
    GENERATION_DEFAULT_MAX_TOKENS : Optional[int] = None
    GENERATION_DEFAULT_TEMPERATURE : Optional[float] = None
    
     

    VECTOR_DB_BACKEND : Optional[str] = None
    VECTOR_DB_PATH : Optional[str] = None
    VECTOR_DB_DISTANCE_METRIC : Optional[str] = None 
    # when set, the client talks to a Qdrant server instead of the embedded local storage
    # the embedded mode allows only one process to open the storage folder at a time
    VECTOR_DB_URL : Optional[str] = None
    VECTOR_DB_API_KEY : Optional[str] = None
    VECTOR_DB_TIMEOUT : Optional[int] = None
    
    #URL LOADER
    URL_REQUEST_TIMEOUT : int = 15
    URL_MAX_REDIRECTS : int = 5
    

    
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)
        
        
@lru_cache
def get_settings():
    return  Settings()                          
# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env")        
        