from sqlalchemy.future import select
from sqlalchemy import func

from .BaseDataModel import BaseDataModel    
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client = db_client
        
        
     
    @classmethod  
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance 

   
                 
    
    
    async def create_project(self, project: Project) -> str:
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)

            await session.commit()
            await session.refresh(project)
        return project
        
               
    
    
    async def get_project_or_create(self, project_id: int) -> Project:
        
        async with self.db_client() as session:
            async with session.begin():
                query = select(Project).where(Project.project_id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                if project is None:
                    project = Project(project_id=project_id)
                    project = await self.create_project(project=project)
                    return project
                else:
                    return project
                
        
        
    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> tuple[list[Project], int]:
        # Calculate the number of documents to skip based on the page and page_size
        
        async with self.db_client() as session:
            async with session.begin():  
                
                total_document = await session.execute(select(func.count(Project.project_id))).scalar_one()
                total_pages = (total_document + page_size - 1) // page_size  # Calculate total pages
                
                query = select(Project).offset((page - 1) * page_size).limit(page_size)
                projects = await session.execute(query).scalars().all()
                
                return projects, total_pages
         
          