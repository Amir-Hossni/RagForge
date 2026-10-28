from openai import AsyncOpenAI

from ..LLMinterface import LLMinterface
from ..LLMEnums import NvidiaEnums, DocumentTypeEnums
from ..LLMErrors import LLMProviderError, EmbeddingError

class NvidiaProvider(LLMinterface):
    
    PROVIDER_NAME = "NVIDIA"
    ROLES = NvidiaEnums
    
    def __init__(self, api_key: str, api_url: str="https://integrate.api.nvidia.com/v1", 
                 default_input_max_characters: int=1000,
                 default_generation_max_tokens: int=1000,
                 default_generation_temperature: float=0.1):
        
        super().__init__(
            api_key=api_key,
            default_input_max_characters=default_input_max_characters,
            default_generation_max_tokens=default_generation_max_tokens,
            default_generation_temperature=default_generation_temperature
        )
        
        self.api_url = api_url
        
        # NVIDIA NIM caps the number of texts per embedding request
        self.embedding_batch_size = 50
        
        # NVIDIA NIM is OpenAI-compatible, so the OpenAI SDK is used with NVIDIA's base url
        self.client = AsyncOpenAI(
            api_key = self.api_key,
            base_url = self.api_url if self.api_url and len(self.api_url) else None
        )
     
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        
        try:
            # NVIDIA NIM takes max_tokens, not OpenAI's max_completion_tokens
            response = await self.client.chat.completions.create(
                model = self.generation_model_id,
                messages = messages,
                max_tokens = max_output_tokens,
                temperature = temperature
            )
        except Exception as e:
            raise LLMProviderError(f"NVIDIA generation failed: {e}") from e
        
        if not response or not response.choices or not response.choices[0].message.content:
            finish_reason = response.choices[0].finish_reason if response and response.choices else None
            raise LLMProviderError(f"NVIDIA returned no text (finish_reason={finish_reason})")
        
        return response.choices[0].message.content
     
    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        
        # NVIDIA embedding models are asymmetric: passages and queries are embedded differently
        input_type = NvidiaEnums.QUERY.value if document_type == DocumentTypeEnums.QUERY.value else NvidiaEnums.DOCUMENT.value
        
        try:
            response = await self.client.embeddings.create(
                model = self.embedding_model_id,
                input = texts,
                extra_body = {"input_type": input_type, "truncate": "END"}
            )
        except Exception as e:
            raise EmbeddingError(f"NVIDIA embedding failed: {e}") from e
        
        if not response or not response.data:
            raise EmbeddingError("NVIDIA returned no embeddings")
        
        # each item carries its own index, do not rely on the response order
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
