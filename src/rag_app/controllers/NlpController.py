from typing import List


from .BaseController import BaseController
from .ProjectController import ProjectController
from ..models import Project, DataChunk, Asset
from ..stores.llm import DocumentTypeEnums


class NLPController(BaseController):
    
    def __init__(self, vectordb_client, generation_client, embedding_client, templateparser=None):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.templateparser = templateparser
        
    def create_collection_name(self, project_id: str):
        # Create a unique collection name based on the project ID
        return f"collection_{project_id}".strip()      
    
    
    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)\
            
            
    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
        return collection_info
    
    
    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk],chunks_ids: List[int] , do_reset: bool = False):
        # Create a unique collection name based on the project ID   
        collection_name = self.create_collection_name(project.project_id)
        
        # manage items
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]
        vectors = await self.embedding_client.embed_text(
            texts, document_type=DocumentTypeEnums.DOCUMENT.value
        )
        
        # create collection if not exists   
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
            
        )
        
        # index data into the collection
        _ = self.vectordb_client.insert_many(
                    collection_name=collection_name,
                    texts=texts,
                    metadata=metadata,
                    vectors=vectors,
                    record_ids = chunks_ids
                    )
        
        return True
        
        
    async def search_vector_db_collection(self, project: Project, text: str, limit: int=5): 
        
        # get collection name 
        collection_name = self.create_collection_name(project_id=project.project_id)
        
        # get text embedding vector
        vectors = await self.embedding_client.embed_text(
            texts = [text],
            document_type = DocumentTypeEnums.QUERY.value
            
        )
        
        if not vectors or len(vectors) == 0:
            return False
        vector = vectors[0]
        # db semantic searce   
        
        results = self.vectordb_client.search_by_vector(
            collection_name = collection_name,
            vector = vector, 
            limit = limit
        )
        
        if results is None:
            return False
        
        return results
    
    async def answer_rag_question(self, project: Project, query: str, limit: int=5):
        
        answer, full_prompt, chat_history = None, None, None
        
        # retrieve related Doc
        
        retrieve_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit
        )
        
        if not retrieve_documents:
            return answer, full_prompt, chat_history
        
        
        # costruct LLM prompt
        
        system_prompt = self.templateparser.get("rag", "system_prompt")
        
        document_prompt = "\n".join([
            self.templateparser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": doc.text
                })
            
            for idx, doc in enumerate(retrieve_documents)
        ])
        
        footer_prompt = self.templateparser.get("rag", "footer_prompt")
        
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.ROLES.SYSTEM.value
            ) 
        ]
        
        full_prompt = "\n\n".join([document_prompt, f"## Question:\n{query}", footer_prompt])
        
        answer = await self.generation_client.generate_text(prompt=full_prompt, chat_history=chat_history)
        
        return answer, full_prompt, chat_history
        
        