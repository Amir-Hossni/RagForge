from enum import Enum

class ResponseSignal(Enum):
    
    
    FILE_VALIDATED_SUCCSESS = "file_validated_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED =  "file_size_exceeded"
    FILE_UPLOADE_SUCCSESS = "file_upload_success"
    FILE_PLOADED_FAILED = "file_uploaded_failed"
    PROCESSING_success = "processing_success"
    PROCESSING_FAILED = "processing_failed"
    