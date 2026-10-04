from .LLMEnums import LLMEnums

from .providers import OpenAiProvider,CoHereProvider


class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config
        
        
    def create(self, provider_name: str):
        if provider_name == LLMEnums.OPENAI.value.lower():
                return OpenAiProvider(
                    api_key = self.config.OPENAI_API_KEY,
                    api_url = self.config.OPENAI_API_URL,
                    default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                    default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                    default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
                )
        
        elif provider_name == LLMEnums.COHERE.value.lower():
            return CoHereProvider(
                api_key = self.config.COHERE_API_KEY,
                default_input_max_characters = self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_tokens = self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature = self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        return None
        
        