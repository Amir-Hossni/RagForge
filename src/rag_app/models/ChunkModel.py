from bson import ObjectId

from sqlalchemy.future import select
from sqlalchemy import delete

from .BaseDataModel import BaseDataModel    
from .db_schemes import DataChunk


class ChunkModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client = db_client        
        
        
    @classmethod  
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance 

    
    async def create_chunk(self, chunk: DataChunk) -> str:
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)

            await session.commit()
            await session.refresh(chunk)
        return chunk
      
    
    
    async def get_chunk_id(self, chunk_id: str) -> DataChunk | None:
        
        async with self.db_client() as session:
            result =  await session.execute(select(DataChunk).where(DataChunk.chunk_id == chunk_id))
            chunk = result.scalar_one_or_none()
        return chunk
    
        
     # to  insert multiple chunks at once, we can use bulk_write method of pymongo     
    async def insert_chunks_bulk(self, chunks: list,batch_size: int = 1000) -> int:
        
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
                await session.commit()
            return len(chunks)    
                
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        
        async with self.db_client() as session:
            result =  await session.execute(delete(DataChunk).where(DataChunk.chunk_id == project_id))
            await session.commit()
        return result.rowcount
  
    
    async def delete_chunks_by_asset_id(self, asset_id: ObjectId) -> int:
        async with self.db_client() as session:
            result =  await session.execute(delete(DataChunk).where(DataChunk.chunk_id == asset_id))
            await session.commit()
        return result.rowcount
    
    async def get_project_chunks(self, project_id: ObjectId, page_num: int=1, page_size: int=50):
        
        async with self.db_client() as session:
            stmt = select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_num - 1) * page_size).limit(page_size)
            results = await session.execute(stmt)
            records = results.scalars().all()
        return records