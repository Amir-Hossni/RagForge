from fastapi import  APIRouter , Depends, UploadFile , status
from fastapi.responses import JSONResponse
import aiofiles
import logging

from ..helper import get_settings , Settings
from ..controllers import DataController
from ..controllers import ProjectController
from ..models import ResponseSignal


logger = logging.getLogger('uvicorn_error')


data_router = APIRouter( 
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)


@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)
                      
                    ):
    data_controller = DataController()
    
    #validate file properties
    is_valid , result_signal = data_controller.validate_uploaded_file(file=file)
    # return {"validation": is_valid ,
    #         "signal": result_signal
    #         }
    
    if not is_valid:
            return JSONResponse(
                status_code= status.HTTP_400_BAD_REQUEST,
                content={"signal" : result_signal
                }
            )
    
    

    file_path , file_id = data_controller.generate_unique_path(
        original_file_name=file.filename,
        project_id=project_id
        )
    
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"error while uploading file{e}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal" : ResponseSignal.FILE_PLOADED_FAILED.value
            }
        )       
    
    
    return JSONResponse(
                    content={
                        "signal" : ResponseSignal.FILE_UPLOADE_SUCCSESS.value,
                        "file_id" : file_id
                    }
                )        
            