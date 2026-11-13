from enum import Enum


class LLMEnums(Enum):
    
    OPENAI = "OPENAI"
    COHERE = "COHERE"
    OLLAMA = "OLLAMA"
    NVIDIA = "NVIDIA"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    
    
class OpenAIEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"    
    
    
class CohereEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"  
        
    DOCUMENT = "search_document"
    QUERY = "search_query"
    
    
class OllamaEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
    
class NvidiaEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
    DOCUMENT = "passage"
    QUERY = "query"
    
    
class AnthropicEnums(Enum):
    
    # the system prompt is a separate argument, not a message
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
    
class GoogleEnums(Enum):
    
    # the system prompt is a separate argument (system_instruction), not a message
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "model"
    
    DOCUMENT = "RETRIEVAL_DOCUMENT"
    QUERY = "RETRIEVAL_QUERY"
    
    
class DocumentTypeEnums(Enum):
    
    PDF = "PDF"
    DOCUMENT = "document"
    QUERY = "query"
    DOCX = "DOCX"
    TXT = "TXT"
    CSV = "CSV"
    JSON = "JSON"
    HTML = "HTML"
    XML = "XML"
    MARKDOWN = "MARKDOWN"    