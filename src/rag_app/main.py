from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from .routes import base , data, nlp
from .helper import get_settings
from .stores.llm import LLMProviderFactory , TemplateParser
from .stores.vectorDB import VectorDBProviderFactory  

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    settings = get_settings()

    app.mongodb_conn = AsyncMongoClient(settings.MONGODB_URI)
    app.db_client = app.mongodb_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(settings)    
    
    #generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    #embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID, embedding_size=settings.EMBEDDING_MODEL_SIZE)

    
    #vector db client 
    app.vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    if app.vectordb_client is None:
        raise ValueError(f"Unsupported VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND}")
    app.vectordb_client.connect()
    
    app.templateparser = TemplateParser(
        language=settings.PRIMARY_LANGUAGE,
        default_language=settings.DEFAULT_LANGUAGE
    )

    yield

    # shutdown
    app.mongodb_conn.close()
    app.vectordb_client.disconnect() 

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)

