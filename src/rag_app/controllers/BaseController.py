from ..helper.config import get_settings 
from pathlib import Path
import random
import string


class BaseController:
    
    
    def __init__(self):
        
        self.app_settings = get_settings()
        
        self.base_dir = Path(__file__).resolve().parent.parent
        self.file_dir = self.base_dir / "assets" / "files"
        
        self.db_dir = self.base_dir / "assets" / "db"   
        
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))        
    

    def get_db_path(self, db_name: str):
        database_path = self.db_dir / db_name
        
        if not database_path.exists():
            database_path.mkdir(parents=True, exist_ok=True)
            
        return database_path