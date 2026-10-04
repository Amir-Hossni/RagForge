from fastapi import  APIRouter , Depends, UploadFile , status , Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
import aiofiles
from bson import ObjectId
import logging
from pathlib import Path


from ..helper import get_settings , Settings
from ..controllers import DataController, ProcessController, ProjectController
from ..controllers.ProcessController import URLValidationError
from .schemes.data import ProcessRequest, URLRequest
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
    if not project_id.isalnum():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_ID_INVALID.value
            }
        )
    
    data_controller = DataController()
    
    #validate file properties
    is_valid , result_signal = data_controller.validate_uploaded_file(file=file)
    
    if not is_valid:
            return JSONResponse(
                status_code= status.HTTP_400_BAD_REQUEST,
                content={"signal" : result_signal
                }
            )
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create(project_id=project_id)
    
    

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
        
        # remove the partially written file
        Path(file_path).unlink(missing_ok=True)
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal" : ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )       
    
    # store assest record in database       
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
  
    asset_resource = Asset(
        asset_project_id= project.id,
        asset_type= AssetTypeEnum.FILE.value,
        asset_name= file_id,
        asset_size= Path(file_path).stat().st_size
    )
    
    asset_record = await asset_model.create_asset(asset=asset_resource)
    
    return JSONResponse(
                    content={
                        "signal" : ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                        "file_id" : str(asset_record.id)
                    }
                )        
            
            
            
@data_router.post("/upload-url/{project_id}")
async def upload_url(request: Request, project_id: str, url_request: URLRequest):
    # the URL is stored as an asset only, its content is fetched in memory while processing
    
    if not project_id.isalnum():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_ID_INVALID.value
            }
        )
    
    url = str(url_request.url)
    
    try:
        await ProcessController.validate_public_url(url)
    except URLValidationError as e:
        logger.error(f"url not allowed: {url} - {e}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.URL_NOT_ALLOWED.value
            }
        )
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create(project_id=project_id)
    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    # (asset_name, asset_project_id) is a unique index
    asset_record = await asset_model.get_asset_record(asset_project_id=project.id, asset_name=url)
    
    if asset_record is not None:
        return JSONResponse(
            content={
                "signal": ResponseSignal.URL_ALREADY_EXISTS.value,
                "file_id": str(asset_record.id)
            }
        )
    
    asset_resource = Asset(
        asset_project_id= project.id,
        asset_type= AssetTypeEnum.URL.value,
        asset_name= url
    )
    
    asset_record = await asset_model.create_asset(asset=asset_resource)
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.URL_ADDED_SUCCESS.value,
            "file_id": str(asset_record.id)
        }
    )
    
    

@data_router.post("/process/{project_id}")  
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest):    
    
    
    if not project_id.isalnum():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_ID_INVALID.value
            }
        )
    
    chunk_size= process_request.chunk_size
    overlap_size= process_request.overlap_size
    do_reset= process_request.do_reset
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)    
            
    project = await project_model.get_project_or_create(project_id=project_id) 
    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    project_file_ids = {}
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(asset_project_id=project.id, asset_name=process_request.file_id)
        
        # /upload and /upload-url return the asset id, so accept it as well as the asset name
        if asset_record is None and ObjectId.is_valid(process_request.file_id):
            asset_record = await asset_model.get_asset_by_id(asset_project_id=project.id, asset_id=process_request.file_id)
        
        if asset_record is None:
             return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value
                }
            )
            
        project_file_ids = {
            asset_record.id: (asset_record.asset_name, asset_record.asset_type)
        }
        
    else:
        
        
        project_files = []
        for asset_type in (AssetTypeEnum.FILE.value, AssetTypeEnum.URL.value):
            project_files += await asset_model.get_all_project_assets(
                asset_project_id=project.id,
                asset_type=asset_type
            )
        
        project_file_ids = {
            record.id: (record.asset_name, record.asset_type)
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
    
    for asset_id, (file_id, asset_type) in project_file_ids.items():
        
        if asset_type == AssetTypeEnum.URL.value:
            try:
                file_content = await process_controller.get_url_content(url=file_id)
            except Exception as e:
                logger.error(f"error while fetching url: {file_id} - {e}")
                continue
        else:
            # file parsing is blocking, run it in a thread to keep the event loop free
            try:
                file_content = await run_in_threadpool(process_controller.get_file_content, file_id=file_id)
            except Exception as e:
                logger.error(f"error while reading file: {file_id} - {e}")
                continue
        
        if file_content is None:
            logger.error(f"error while processing file: {file_id}")
            continue
        
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        if file_chunks is None or len(file_chunks) == 0:
            logger.error(f"no chunks were generated for file: {file_id}")
            continue
            
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
            
        
        # re-processing an asset replaces its old chunks instead of duplicating them,
        # old chunks are removed only after the new ones were generated successfully
        _ = await chunk_model.delete_chunks_by_asset_id(asset_id=asset_id)
        
        num_records += await chunk_model.insert_chunks_bulk(chunks=file_chunks_records)
        num_files += 1

    if num_files == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )

    return JSONResponse(
        content={
                    "signal": ResponseSignal.PROCESSING_SUCCESS.value,
                    "inserted_chunks": num_records,
                    "processed_files": num_files
                }   
    )
        
   
                                                        