from fastapi import  APIRouter , Depends, UploadFile , status , Request
from fastapi.responses import JSONResponse
import aiofiles
import logging
from pathlib import Path


from ..helper import get_settings , Settings
from ..controllers import DataController, ProcessController, ProjectController
from .schemes.data import ProcessRequest
from ..models import ResponseSignal, ProjectModel, ChunkModel, DataChunk , AssetModel , Asset ,AssetTypeEnum  


logger = logging.getLogger('uvicorn_error')


data_router = APIRouter( 
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)
                    ):
    prject_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    
    project = await prject_model.get_project_or_create(project_id=project_id)
    
    data_controller = DataController()
    
    #validate file properties
    is_valid , result_signal = data_controller.validate_uploaded_file(file=file)
    
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
    
    # store assest record in database       
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
  
    asset_rescorce = Asset(
        asset_project_id= project.id,
        asset_type= AssetTypeEnum.FILE.value,
        asset_name= file_id,
        asset_size= Path(file_path).stat().st_size
    )
    
    asset_record = await asset_model.create_asset(asset=asset_rescorce)
    
    return JSONResponse(
                    content={
                        "signal" : ResponseSignal.FILE_UPLOADE_SUCCSESS.value,
                        "file_id" : str(asset_record.id)
                    }
                )        
            
            
            

@data_router.post("/process/{project_id}")  
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest):    
    
    
    # file_id = process_request.file_id
    chunk_size= process_request.chunk_size
    overlap_size= process_request.overlap_size
    do_reset= process_request.do_reset
    
    prject_model = await ProjectModel.create_instance(db_client=request.app.db_client)    
            
    project = await prject_model.get_project_or_create(project_id=project_id) 
    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    project_file_ids = {}
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(asset_project_id=project.id, asset_name=process_request.file_id)
        
        if asset_record is None:
             return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value
                }
            )
            
        project_file_ids = {
            asset_record.id: asset_record.asset_name
        }
        
    else:
        
        
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value
        )
        
        project_file_ids = {
            record.id: record.asset_name
            for record in project_files
        }

            
    if len(project_file_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value
            }
        )
    
    
    
    process_controller = ProcessController(project_id=project_id)  
    
    
    num_records = 0
    num_files = 0
    
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client) 
    if do_reset == 1:
        _  = await chunk_model.delete_chunks_by_project_id(project_id=project.id)  
    
    for asset_id, file_id in project_file_ids.items():
        
        file_contet = process_controller.get_file_content(file_id=file_id)
        
        if file_contet is None:
            logger.error(f"error while processing file: {file_id}")
            continue
        
        file_chunks = process_controller.process_file_contet(
            file_content=file_contet,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                contet={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }  
            )
            
        file_chunks_records = [
            DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=project.id,
            chunk_asset_id=asset_id
            )
            
            for i, chunk in enumerate(file_chunks)
                            ]
            
        
        num_records += await chunk_model.insert_chunks_bulk(chunks=file_chunks_records)
        num_files += 1
        
    return JSONResponse(
        content={
                    "signal": ResponseSignal.PROCESSING_SUCCSESS.value,
                    "inserted_chunks": num_records,
                    "processed_files": num_files
                }   
    )
        
   
                                                        