from anthropic import AsyncAnthropic

from ..LLMinterface import LLMinterface
from ..LLMEnums import AnthropicEnums
from ..LLMErrors import LLMProviderError, EmbeddingError, UnsupportedProviderError

class AnthropicProvider(LLMinterface):
    
    PROVIDER_NAME = "Anthropic"
    ROLES = AnthropicEnums
    
    def __init__(self, api_key: str,  
                 default_input_max_characters: int=1000,
                 default_generation_max_tokens: int=1000,
                 default_generation_temperature: float=0.1,
                 default_think: bool | str | None = None):
        
        super().__init__(
            api_key=api_key,
            default_input_max_characters=default_input_max_characters,
            default_generation_max_tokens=default_generation_max_tokens,
            default_generation_temperature=default_generation_temperature,
            default_think=default_think
        )
        
        # async client, so waiting for the model does not block the FastAPI event loop
        self.client = AsyncAnthropic(api_key=self.api_key)
        
     
    def set_embedding_model(self, model_id: str, embedding_size: int):
        # fail at startup if EMBEDDING_BACKEND is set to Anthropic
        raise UnsupportedProviderError("Anthropic has no embeddings API, choose another EMBEDDING_BACKEND")
     
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        
        # temperature is accepted for interface parity but not sent:
        # the current Anthropic SDK no longer exposes sampling parameters
        
        # the system prompt is a separate argument, not a message
        system_prompt = "\n\n".join(
            message["content"] for message in messages
            if message["role"] == AnthropicEnums.SYSTEM.value
        )
        messages = [
            message for message in messages
            if message["role"] != AnthropicEnums.SYSTEM.value
        ]
        
        request = {
            "model": self.generation_model_id,
            "messages": messages,
            # max_tokens is required by Anthropic
            "max_tokens": max_output_tokens or 1024
        }
        if system_prompt:
            request["system"] = system_prompt
        
        if self.default_think is not None:
            request["think"] = self.default_think
        
        try:
            response = await self.client.messages.create(**request)
        except Exception as e:
            raise LLMProviderError(f"Anthropic generation failed: {e}") from e
        
        # content is a list of blocks, join the text ones and skip "thinking" blocks
        blocks = response.content if response and response.content else []
        text = "".join(block.text for block in blocks if getattr(block, "type", None) == "text")
        
        if not text:
            stop_reason = getattr(response, "stop_reason", None)
            raise LLMProviderError(f"Anthropic returned no text (stop_reason={stop_reason})")
        
        return text
     
    async def embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        # overrides the shared embed_text so the error is clear even before an embedding model is set
        raise EmbeddingError("Anthropic has no embeddings API, choose another EMBEDDING_BACKEND")

    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        raise EmbeddingError("Anthropic has no embeddings API, choose another EMBEDDING_BACKEND")
