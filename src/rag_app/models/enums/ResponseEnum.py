from enum import Enum

class ResponseSignal(Enum):
    
    
    FILE_VALIDATED_SUCCESS = "file_validated_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED =  "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_uploaded_failed"
    PROCESSING_SUCCESS = "processing_success"
    PROCESSING_FAILED = "processing_failed"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"
    URL_ADDED_SUCCESS = "url_added_success"
    URL_ALREADY_EXISTS = "url_already_exists"
    URL_NOT_ALLOWED = "url_not_allowed"
    FILE_EMPTY = "file_empty"
    PROJECT_ID_INVALID = "project_id_must_be_alphanumeric"
    PROJECT_NOT_FOUND = "project_not_found"
    INSERT_INTO_VECTORDB_ERROR = "insert_into_vectordb_error"
    INSERT_INTO_VECTORDB_SUCCSESS = "insert_into_vectordb_success"
    VECTORDB_COLLECTION_RETRIVED = "vectordb_collection_retrived"
    VECTORDB_SEARCH_ERROR = "vectordb_search_error"
    VECTORDB_SEARCH_SUCCESS = "vectordb_search_success"