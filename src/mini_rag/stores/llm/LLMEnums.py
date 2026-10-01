from enum import Enum


class LLMEnums(Enum):
    
    OPENaI = "OPENAI"
    COHERE = "COHERE"
    
    
class OpenAIEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"    