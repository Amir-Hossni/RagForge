from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from .routes import base , data
from .helper import get_settings

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URI)
    app.db_client = app.mongodb_conn[settings.MONGODB_DATABASE]
    

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_conn.close()


app.include_router(base.base_router)
app.include_router(data.data_router)


