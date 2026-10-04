from .BaseDataModel import BaseDataModel    
from bson import ObjectId
from pymongo import InsertOne

from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum

class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNKS_NAME.value]
        
        
        
    @classmethod  
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance 

    async def init_collection(self) -> None:   
        all_collections = await self.db_client.list_collection_names()
        
        if DataBaseEnum.COLLECTION_CHUNKS_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNKS_NAME.value]
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                    )    
    
    async def create_chunk(self, chunk: DataChunk) -> str:
        result = await self.collection.insert_one(
                    chunk.model_dump(
                        by_alias=True,
                        exclude_none=True
                    )
                )
             
        chunk_id = str(result.inserted_id)

        return chunk_id 
    
    
    async def get_chunk_id(self, chunk_id: str) -> DataChunk | None:
        
        result = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        
        if result is None:
            return None
        else:
            return DataChunk(**result)
        
     # to  insert multiple chunks at once, we can use bulk_write method of pymongo     
    async def insert_chunks_bulk(self, chunks: list,batch_size: int = 1000) -> int:
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            operations = [InsertOne(chunk.model_dump(by_alias=True, exclude_none=True)) for chunk in batch]
            await self.collection.bulk_write(operations)
    
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        result = await self.collection.delete_many({"chunk_project_id": project_id})
        return result.deleted_count
    
    async def delete_chunks_by_asset_id(self, asset_id: ObjectId) -> int:
        result = await self.collection.delete_many({"chunk_asset_id": asset_id})
        return result.deleted_count