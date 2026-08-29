from fastapi import UploadFile
from .BaseController import BaseController
from ..models import ResponseSignal
from pathlib import Path

class ProjectController(BaseController):
    
    def __init__(self):
        super().__init__()
        
        
    def get_project_path(self, project_id: str):
        
        project_dir = self.file_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        return project_dir