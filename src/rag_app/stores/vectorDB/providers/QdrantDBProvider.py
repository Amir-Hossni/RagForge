from qdrant_client import QdrantClient ,models
import logging
import uuid
from typing import List 

from src.rag_app.models import RetrievedDocument
from ..VectorDBInterFace import VectorDBInterFace
from ..VectorDBEnums import  DistanceMetricEnums


class QdrantDBProvider(VectorDBInterFace):
    def __init__(self, db_path: str, distance_metric : str, 
                 db_url: str = None, api_key: str = None, timeout: int = None):
        super().__init__()

        
        self.db_path = db_path
        self.distance_metric = distance_metric
        self.db_url = db_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        if self.distance_metric == DistanceMetricEnums.COSINE.value:
            self.distance_metric = models.Distance.COSINE
        elif self.distance_metric == DistanceMetricEnums.DOT.value: 
            self.distance_metric = models.Distance.DOT
        else:
            raise ValueError(f"Unsupported distance metric: {distance_metric}")
        
        
      
    def connect(self):
        try:
            if self.db_url:
                # a Qdrant server allows concurrent access, the embedded storage does not
                self.client = QdrantClient(
                    url=self.db_url,
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            else:
                self.client = QdrantClient(path=self.db_path)
        except RuntimeError as e:
            # the embedded storage keeps an exclusive lock on the folder,
            # so a second process (or a stale one) makes the startup fail
            raise RuntimeError(
                f"Could not open the Qdrant storage folder '{self.db_path}': {e}\n"
                "The embedded Qdrant storage allows only one process at a time. "
                "Stop the other process that uses the same folder, or set VECTOR_DB_URL "
                "in the .env file to use a Qdrant server instead."
            ) from e

    
    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
    
    
    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name) 
    
    
    def list_all_collections(self) -> List:
        return self.client.get_collections().collections

        
    
    def get_collection_info(self, collection_name: str) :
        # the collection may not be created yet, return None instead of raising
        # so the route can answer with a clean 404 instead of a 500
        if not self.is_collection_exists(collection_name):
            self.logger.warning(f"Collection '{collection_name}' does not exist.")
            return None
            
        return self.client.get_collection(collection_name=collection_name)  
    
    
    
    def delete_collection(self, collection_name: str):
        
        if not self.is_collection_exists(collection_name):
            self.logger.warning(f"Collection '{collection_name}' does not exist.")
            return False

        self.client.delete_collection(collection_name=collection_name)  
        return True
        
            
     
    
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
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        
        try:
            # the point id must be an int or an uuid string, the id is set on the point itself
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
            
        if len(record_ids) != len(texts):
            self.logger.error(
                f"record_ids length ({len(record_ids)}) does not match texts length ({len(texts)})"
            )
            return False
            
        if not self.is_collection_exists(collection_name):
            self.logger.error(f"Collection '{collection_name}' does not exist.")
            return False
            
            
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
           
        
    
    
    def search_by_vector(self, collection_name: str, vector: list, limit: int=5) -> RetrievedDocument:
        # searching in a collection that was never created is not an error, it returns no results
        if not self.is_collection_exists(collection_name):
            self.logger.warning(f"Collection '{collection_name}' does not exist.")
            return []
            
        results =  self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        ).points
        
        if not results or len(results) == 0:
            return []
        
        return [
            RetrievedDocument(**{
                "score": result.score,
                "text": result.payload["text"]
            })
            for result in results
        ]
            
        
            
