from ..helper.config import get_settings 
from pathlib import Path
import random
import string


class BaseController:
    
    
    def __init__(self):
        
        self.app_settings = get_settings()
        
        self.base_dir = Path(__file__).resolve().parent.parent
        self.file_dir = self.base_dir / "assets" / "files"
        
        
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))        