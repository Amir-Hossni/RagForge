from ollama import AsyncClient

from ..LLMinterface import LLMinterface
from ..LLMEnums import OllamaEnums
from ..LLMErrors import LLMProviderError, EmbeddingError

class OllamaProvider(LLMinterface):
    
    PROVIDER_NAME = "Ollama"
    ROLES = OllamaEnums
    
    def __init__(self, api_url: str="http://localhost:11434", 
                 default_input_max_characters: int=1000,
                 default_generation_max_tokens: int=1000,
                 default_generation_temperature: float=0.1):
        
        # Ollama runs locally, so there is no api key
        super().__init__(
            default_input_max_characters=default_input_max_characters,
            default_generation_max_tokens=default_generation_max_tokens,
            default_generation_temperature=default_generation_temperature
        )
        
        self.api_url = api_url
        
        # async client, so waiting for the model does not block the FastAPI event loop
        self.client = AsyncClient(host=self.api_url if self.api_url and len(self.api_url) else None)
     
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        
        # Ollama names the output limit num_predict
        options = {}
        if max_output_tokens is not None:
            options["num_predict"] = max_output_tokens
        if temperature is not None:
            options["temperature"] = temperature
        
        try:
            response = await self.client.chat(
                model = self.generation_model_id,
                messages = messages,
                options = options
            )
        except Exception as e:
            raise LLMProviderError(
                f"Ollama generation failed at {self.api_url}: {e} "
                "(is `ollama serve` running and has the model been pulled?)"
            ) from e
        
        if not response or not response.message or not response.message.content:
            done_reason = getattr(response, "done_reason", None)
            raise LLMProviderError(f"Ollama returned no text (done_reason={done_reason})")
        
        return response.message.content
     
    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        
        # Ollama embeddings are symmetric, document_type is accepted for interface parity
        try:
            response = await self.client.embed(
                model = self.embedding_model_id,
                input = texts
            )
        except Exception as e:
            raise EmbeddingError(
                f"Ollama embedding failed at {self.api_url}: {e} "
                "(is `ollama serve` running and has the model been pulled?)"
            ) from e
        
        if not response or not response.embeddings:
            raise EmbeddingError("Ollama returned no embeddings")
        
        return [list(vector) for vector in response.embeddings]
