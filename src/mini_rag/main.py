from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import base , data
from .helper import get_settings
from .stores.llm import LLMProviderFactory

app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URI)
    app.db_client = app.mongodb_conn[settings.MONGODB_DATABASE]
    
    llm_provider_factory = LLMProviderFactory(settings)
    
    #generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND) 
    app.get_generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
    
    #embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND) 
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID, embedding_size=settings.EMBEDDING_MODEL_SIZE)    
    

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_conn.close()


app.include_router(base.base_router)
app.include_router(data.data_router)


