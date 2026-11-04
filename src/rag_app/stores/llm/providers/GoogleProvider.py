from google import genai
from google.genai import types

from ..LLMinterface import LLMinterface
from ..LLMEnums import GoogleEnums, DocumentTypeEnums
from ..LLMErrors import LLMProviderError, EmbeddingError

class GoogleProvider(LLMinterface):
    
    PROVIDER_NAME = "Google"
    ROLES = GoogleEnums
    
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
        
        # Gemini caps the number of texts per embedding request
        self.embedding_batch_size = 100
        
        # the async methods live under client.aio
        self.client = genai.Client(api_key=self.api_key)
     
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        
        # the system prompt is a separate argument (system_instruction), not a message
        system_prompt = "\n\n".join(
            message["content"] for message in messages
            if message["role"] == GoogleEnums.SYSTEM.value
        )
        
        # Gemini calls the assistant role "model"
        contents = [
            types.Content(
                role = GoogleEnums.ASSISTANT.value if message["role"] in (GoogleEnums.ASSISTANT.value, "assistant") else GoogleEnums.USER.value,
                parts = [types.Part.from_text(text=message["content"])]
            )
            for message in messages
            if message["role"] != GoogleEnums.SYSTEM.value
        ]
        
        config_kwargs = {
            "system_instruction": system_prompt or None,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature
        }

        if self.default_think is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=self.default_think
            )

        config = types.GenerateContentConfig(**config_kwargs)
        
        try:
            response = await self.client.aio.models.generate_content(
                model = self.generation_model_id,
                contents = contents,
                config = config
            )
        except Exception as e:
            raise LLMProviderError(f"Google generation failed: {e}") from e
        
        # response.text joins the text parts and skips the "thought" parts
        if not response or not response.text:
            candidates = getattr(response, "candidates", None) or []
            finish_reason = candidates[0].finish_reason if candidates else None
            raise LLMProviderError(f"Google returned no text (finish_reason={finish_reason})")
        
        return response.text
     
    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        
        task_type = GoogleEnums.QUERY.value if document_type == DocumentTypeEnums.QUERY.value else GoogleEnums.DOCUMENT.value
        
        try:
            response = await self.client.aio.models.embed_content(
                model = self.embedding_model_id,
                contents = texts,
                config = types.EmbedContentConfig(task_type=task_type)
            )
        except Exception as e:
            raise EmbeddingError(f"Google embedding failed: {e}") from e
        
        if not response or not response.embeddings:
            raise EmbeddingError("Google returned no embeddings")
        
        return [list(embedding.values) for embedding in response.embeddings]
    
    async def aclose(self):
        # the async client of google-genai closes with aclose()
        await self.client.aio.aclose()
