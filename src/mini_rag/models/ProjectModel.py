from .BaseDataModel import BaseDataModel    
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
        
    
    async def create_project(self, project: Project) -> str:
        result = await self.collection.insert_one(
                    project.model_dump(
                        by_alias=True,
                        exclude_none=True
                    )
                )
        project_id = str(result.inserted_id)

        return project_id
        
               
    
    
    async def get_project_or_create(self, project_id: str) -> Project:
        
        record = await self.collection.find_one({"project_id": project_id})
        
        if record is None:
            new_project = Project(project_id=project_id)
            await self.create_project(project=new_project)
            return new_project
        else:
            return Project(**record)
        
        
    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> list[Project]:
        # Calculate the number of documents to skip based on the page and page_size
        
        total_documents  = await self.collection.count_documents({})  # Get the total number of documents in the collection 
        
        # Calculate the total number of pages
        total_pages = total_documents // page_size
        if total_documents % page_size != 0:
            total_pages += 1
            
        
        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)   
        projects = []
        async for record in cursor:
            projects.append(Project(**record))  
            
        return projects, total_pages       
          