import cohere 

from ..LLMinterface import LLMinterface
from ..LLMEnums import CohereEnums , DocumentTypeEnums
from ..LLMErrors import LLMProviderError, EmbeddingError

class CoHereProvider(LLMinterface):
    
    PROVIDER_NAME = "Cohere"
    ROLES = CohereEnums
    
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
        
        # Cohere accepts at most 96 texts per embedding request
        self.embedding_batch_size = 96
        
        # async client, so waiting for the model does not block the FastAPI event loop
        self.client = cohere.AsyncClientV2(api_key=self.api_key)
     
    async def _generate_text(self, messages: list, max_output_tokens: int, temperature: float) -> str:
        
        try:
            request_kwargs = {
                "model": self.generation_model_id,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_output_tokens
            }

            if self.default_think is not None:
                request_kwargs["thinking"] = self.default_think

            response = await self.client.chat(**request_kwargs)
        except Exception as e:
            raise LLMProviderError(f"Cohere generation failed: {e}") from e
        
        # content is a list of blocks, join the text ones and skip "thinking" blocks of reasoning models
        blocks = response.message.content if response and response.message and response.message.content else []
        text = "".join(block.text for block in blocks if getattr(block, "type", None) == "text")
        
        if not text:
            finish_reason = getattr(response, "finish_reason", None)
            raise LLMProviderError(f"Cohere returned no text (finish_reason={finish_reason})")
        
        return text
     
    async def _embed_text(self, texts: list[str], document_type: str=None) -> list[list[float]]:
        
        input_type = CohereEnums.QUERY.value if document_type == DocumentTypeEnums.QUERY.value else CohereEnums.DOCUMENT.value
        
        try:
            response = await self.client.embed(
                model = self.embedding_model_id,
                texts = texts,
                input_type = input_type,
                embedding_types = ["float"],
            )
        except Exception as e:
            raise EmbeddingError(f"Cohere embedding failed: {e}") from e
        
        if not response or not response.embeddings or not response.embeddings.float_:
            raise EmbeddingError("Cohere returned no embeddings")

        return list(response.embeddings.float_)
    
    async def aclose(self):
        # the Cohere async client has no public close(), its httpx client is nested inside
        httpx_client = getattr(getattr(self.client, "_client_wrapper", None), "httpx_client", None)
        httpx_client = getattr(httpx_client, "httpx_client", httpx_client)
        
        if httpx_client is not None and hasattr(httpx_client, "aclose"):
            await httpx_client.aclose()

    
    def construct_prompt(self, prompt: str, role: str):
            return{
                "role": role,
                "content": self._process_text(prompt)
            }