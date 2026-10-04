from enum import Enum


class LLMEnums(Enum):
    
    OPENaI = "OPENAI"
    COHERE = "COHERE"
    
    
class OpenAIEnums(Enum):
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"    
    
    
class CohereEnums(Enum):
    
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"  
        
    DOCUMENT = "search_document"
    QUERY = "search_query"
    
    
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