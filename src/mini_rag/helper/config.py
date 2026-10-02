from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    
    APP_NAME : str
    APP_VERSION : str
    OPENAI_API_KEY : str

    FILE_ALLOWED_TYPES : list[str]
    FILE_MAX_SIZE : int
    FILE_DEFAULT_CHUNK_SIZE : int
    
    MONGODB_URI : str
    MONGODB_DATABASE : str
    
    #LLM PROVIDERS     
    GENERATION_BACKEND : str=None
    EMBEDDING_BACKEND : str=None

    OPENAI_API_KEY : str=None
    OPENAI_API_URL : str=None

    COHERE__API_KEY : str=None

    GENERATION_MODEL_ID : str=None
    EMBEDDING_MODEL_ID : str=None
    EMBEDDING_MODEL_SIZE : int=None

    INPUT_DEFAULT_MAX_CHARACTERS : int=None
    GENERATION_DEFAULT_MAX_TOKENS : int=None
    GENERATION_DEFAULT_TEMPERATURE : float=None
    
    model_config = SettingsConfigDict(env_file=".env")
        
        
def get_settings():
    return  Settings()                          
# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env")        
        