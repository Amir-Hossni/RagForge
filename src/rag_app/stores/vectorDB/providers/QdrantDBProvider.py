from qdrant_client import QdrantClient ,models
import logging
import uuid
from typing import List 


from ..VectorDBInterFace import VectorDBInterFace
from ..VectorDBEnums import  DistanceMetricEnums


class QdrantDBProvider(VectorDBInterFace):
    def __init__(self, db_path: str, distance_metric : str):
        super().__init__()

        
        self.db_path = db_path
        self.distance_metric = distance_metric
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        if self.distance_metric == DistanceMetricEnums.COSINE.value:
            self.distance_metric = models.Distance.COSINE
        elif self.distance_metric == DistanceMetricEnums.DOT.value: 
            self.distance_metric = models.Distance.DOT
        else:
            raise ValueError(f"Unsupported distance metric: {distance_metric}")
        
        
      
    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    
    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
    
    
    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name) 
    
    
    def list_all_collections(self) -> List:
        return self.client.get_collections().collections

        
    
    def get_collection_info(self, collection_name: str) :
        return self.client.get_collection(collection_name=collection_name)  
    
    
    
    def delete_collection(self, collection_name: str):
        
        if not self.is_collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist.")

        self.client.delete_collection(collection_name=collection_name)  
        
            
     
    
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset and self.is_collection_exists(collection_name):
            self.delete_collection(collection_name)
            
        if not self.is_collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_metric)
            )    
            
            return True
        
        return False
    
        
    def insert_one(self, collection_name: str, text: str, vector: list,
                            metadata: dict = None, record_id: str = None):
        if not self.is_collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist.")
        
        try:
            self.client.upload_points(
                collection_name=collection_name,
                points=[models.PointStruct(
                    id=record_id if record_id is not None else str(uuid.uuid4()),
                    vector=vector,
                    payload={
                            "text": text,
                            "metadata": metadata
                        }
                    )
                ]   
                )
        except Exception as e:
            self.logger.error(f"Error inserting record: {e}")
            return False
        
        return True
    
    
    def insert_many(self, collection_name: str, texts: List[str], vectors: list,
                            metadata: list = None, record_ids: list = None, batch_size: int = 50):   
                                
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = [str(uuid.uuid4()) for _ in range(len(texts))]   
            
        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]
            
            batch_records = [
                models.PointStruct(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x],
                        "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]
            
            try:
                self.client.upload_points(
                    collection_name=collection_name,
                    points=batch_records
                )
            except Exception as e:
                self.logger.error(f"Error inserting batch starting at index {i}: {e}")
                return False
            
            
        return True
           
        
    
    
    def search_by_vector(self, collection_name: str, vector: list, limit: int=5) -> list:
        return self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        ).points
        
            
