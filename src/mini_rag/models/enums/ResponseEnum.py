from enum import Enum

class ResponseSignal(Enum):
    
    
    FILE_VALIDATED_SUCCSESS = "file_validated_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED =  "file_size_exceeded"
    FILE_UPLOADE_SUCCSESS = "file_upload_success"
    FILE_PLOADED_FAILED = "file_uploaded_failed"
    PROCESSING_SUCCSESS = "processing_success"
    PROCESSING_FAILED = "processing_failed"
    NO_FILES_ERROR = "not_founf_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"