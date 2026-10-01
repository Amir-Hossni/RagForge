from abc import ABC, abstractmethod

class LLMinterface(ABC):
    
    
    @abstractmethod 
    def set_generation_model(self, model_id: str):
        pass
    
    
    @abstractmethod 
    def set_embedding_model(self, model_id: str, emedding_size: int):
        pass
    
    @abstractmethod 
    def generate_text(self, prompt: str,chat_history: list=[], max_output_tokens: str=None ,temperature: float=None):
        pass
    
    
    @abstractmethod 
    def embed_text(self, text: str, document_type: str=None):
        pass
        
    @abstractmethod 
    def construct_prompt(self, prompt: str, role: StopIteration):
        pass
        