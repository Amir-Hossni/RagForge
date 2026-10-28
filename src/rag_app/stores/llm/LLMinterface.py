from abc import ABC, abstractmethod
import logging

from .LLMErrors import LLMProviderError, EmbeddingError

class LLMinterface(ABC):
    
    # set by every provider: its name (for error messages) and its role enum (OpenAIEnums, CohereEnums, ...)
    PROVIDER_NAME = None
    ROLES = None
    
    @property
    def enums(self):
        # Backward-compatibility alias for ROLES
        return self.ROLES
    
    def __init__(self, api_key: str=None,
                 default_input_max_characters: int=1000,
                 default_generation_max_tokens: int=1000,
                 default_generation_temperature: float=0.1):
        
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_tokens = default_generation_max_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        # max texts per embedding request, None means no limit
        self.embedding_batch_size = None
        
        # the provider creates its own SDK client
        self.client = None
        
        # e.g. "rag_app.stores.llm.providers.OpenAiProvider"
        self.logger = logging.getLogger(type(self).__module__)
    
    
    def _process_text(self, text: str):
        # used for embedding inputs only, generation prompts are not truncated
        # (a RAG prompt holds the retrieved context and the question at its end)
        if not self.default_input_max_characters:
            return text.strip()
        
        return text[:self.default_input_max_characters].strip()
    
    
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
     
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        
        
    def construct_prompt(self, prompt: str, role: str):
        return{
            "role": role,
            "content": prompt
        }
    
    
    async def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: int=None, temperature: float=None) -> str:
        # returns the generated text, raises LLMProviderError on failure (never returns None)
        # the steps shared by all providers are here, the vendor call is in _generate_text
        
        if not self.generation_model_id:
            raise LLMProviderError(f"generation model for {self.PROVIDER_NAME} is not set")
        
        max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_generation_max_tokens
        )
        
        temperature = (
            temperature 
            if temperature is not None
            else self.default_generation_temperature
        )     
        
        # copy so the caller's list is not changed
        chat_history = list(chat_history) if chat_history else []
        chat_history.append(
            self.construct_prompt(prompt=prompt, role=self.ROLES.USER.value)
        )
        
        return await self._generate_text(
            messages=chat_history,
            max_output_tokens=max_output_tokens,
            temperature=temperature
        )
    
    
    async def embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        # embeds a batch of texts, returns one vector per text in the same order
        # the steps shared by all providers are here, the vendor call is in _embed_text
        
        if not self.embedding_model_id:
            raise EmbeddingError(f"embedding model for {self.PROVIDER_NAME} is not set")
        
        if not texts:
            return []
        
        batch_size = self.embedding_batch_size or len(texts)
        
        vectors = []
        for i in range(0, len(texts), batch_size):
            batch = [self._process_text(text) for text in texts[i:i + batch_size]]
            vectors += await self._embed_text(texts=batch, document_type=document_type)
        
        return self.validate_embeddings(texts=texts, vectors=vectors)
    
    
    @abstractmethod 
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        # the only generation code a provider writes: call the vendor and read the text
        # raises LLMProviderError on failure or empty answer
        pass
    
    
    @abstractmethod 
    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        # the only embedding code a provider writes: call the vendor for one batch and read the vectors
        # raises EmbeddingError on failure or empty response
        pass
    
    
    async def aclose(self):
        # release the client's connection pool on shutdown
        # most SDK clients expose an async close(), providers with another name override this
        if self.client is not None and hasattr(self.client, "close"):
            await self.client.close()
    
    
    def validate_embeddings(self, texts: list[str], vectors: list[list[float]]) -> list[list[float]]:
        # vectors are matched to chunks by position, and the vector DB collection has a fixed size
        
        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"{type(self).__name__} returned {len(vectors)} vectors for {len(texts)} texts"
            )
        
        if self.embedding_size and vectors and len(vectors[0]) != self.embedding_size:
            raise EmbeddingError(
                f"{type(self).__name__} returned {len(vectors[0])}-dimensional vectors "
                f"but EMBEDDING_MODEL_SIZE is {self.embedding_size}"
            )
        
        return vectors
