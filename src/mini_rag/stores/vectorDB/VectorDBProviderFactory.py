from .providers import QdrantDBProvider
from .VectorDBEnums import VectorDBBEnums   
from src.mini_rag.controllers.BaseController import BaseController 


class VectorDBProviderFactory:
    
    def __init__(self, config: dict):
        self.config = config
        self.base_controller = BaseController()
        
    def creater(self, provider: str):
        
        if provider == VectorDBBEnums.QDRANT.value:
            db_path = self.base_controller.get_db_path(db_name=self.config.VECTOR_DB_NAME)
            return QdrantDBProvider(
                                    db_path=db_path,
                distance_metric=self.config.VECTOR_DB_DISTANCE_METRIC,      
          )
        
        return None    