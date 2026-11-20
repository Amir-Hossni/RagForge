from bson import ObjectId       

from sqlalchemy.future import select
from sqlalchemy import delete

from .BaseDataModel import BaseDataModel    
from .db_schemes import Asset




class AssetModel(BaseDataModel):
    
    def __init__(self, db_client: object):
            super().__init__(db_client)
            self.db_client = db_client
            
            
    @classmethod  
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance         
    
                    
    async def create_asset(self, asset: Asset) -> Asset:   
        
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)

            await session.commit()
            await session.refresh(asset)
        return asset         
    
    
    async def get_all_project_assets(self, asset_project_id: int, asset_type: str) :
        
        async with self.db_client() as session:  
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_type == asset_type
            )
            results = await session.execute(stmt)
            records = results.scalars().all()
        return records             
    
    async def get_asset_by_id(self, asset_project_id: int, asset_id: int):
        
        async with self.db_client() as session:
            result =  await session.execute(select(Asset).where(Asset.asset_id == asset_id))
            asset = result.scalar_one_or_none()
        return asset
    
    async def get_asset_record(self, asset_project_id: str, asset_name: str):
        
        async with self.db_client() as session:
            stmt = select(Asset).where(
                Asset.asset_project_id == asset_project_id,
                Asset.asset_name == asset_name
            )
            result = await session.execute(stmt)
            asset = result.scalar_one_or_none()
        return asset