from .LLMEnums import LLMEnums
from .LLMErrors import UnsupportedProviderError

from .providers import OpenAiProvider, CoHereProvider, OllamaProvider, NvidiaProvider, AnthropicProvider, GoogleProvider


class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config
        
        
    def create(self, provider: str):
        
        # "openai", "OpenAI" and "OPENAI" are the same provider
        provider_name = str(provider).strip().upper() if provider else ""
        
        if provider_name == LLMEnums.OPENAI.value:
            # fail at startup rather than on the first user request
            if not self.config.OPENAI_API_KEY:
                raise UnsupportedProviderError("OPENAI_API_KEY is not set, so the OpenAI provider cannot be built")
            
            return OpenAiProvider(
                    api_key = self.config.OPENAI_API_KEY,
                    api_url = self.config.OPENAI_API_URL,
                    default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                    default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                    default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
                )
        
        if provider_name == LLMEnums.COHERE.value:
            if not self.config.COHERE_API_KEY:
                raise UnsupportedProviderError("COHERE_API_KEY is not set, so the Cohere provider cannot be built")
            
            return CoHereProvider(
                api_key = self.config.COHERE_API_KEY,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider_name == LLMEnums.OLLAMA.value:
            # runs locally, so there is no api key to check
            return OllamaProvider(
                api_url = self.config.OLLAMA_API_URL,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider_name == LLMEnums.NVIDIA.value:
            if not self.config.NVIDIA_API_KEY:
                raise UnsupportedProviderError("NVIDIA_API_KEY is not set, so the NVIDIA provider cannot be built")
            
            return NvidiaProvider(
                api_key = self.config.NVIDIA_API_KEY,
                api_url = self.config.NVIDIA_API_URL,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider_name == LLMEnums.ANTHROPIC.value:
            if not self.config.ANTHROPIC_API_KEY:
                raise UnsupportedProviderError("ANTHROPIC_API_KEY is not set, so the Anthropic provider cannot be built")
            
            return AnthropicProvider(
                api_key = self.config.ANTHROPIC_API_KEY,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider_name == LLMEnums.GOOGLE.value:
            if not self.config.GOOGLE_API_KEY:
                raise UnsupportedProviderError("GOOGLE_API_KEY is not set, so the Google provider cannot be built")
            
            return GoogleProvider(
                api_key = self.config.GOOGLE_API_KEY,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        raise UnsupportedProviderError(
            f"Unknown LLM provider {provider!r}. Supported: {[p.value for p in LLMEnums]}"
        )
