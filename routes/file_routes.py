from fastapi import APIRouter, Request
from fastapi.params import Depends

from service.file_service import FileService
from auth.jwt import verify_token

file_router = APIRouter()

file_service = FileService()

@file_router.post("/init",dependencies = [Depends(verify_token)])
async def initialize_upload(filename: str):
    response =await file_service.initialize_upload(filename=filename)
    return response


@file_router.post("/upload/{upload_id}",dependencies = [Depends(verify_token)])
async def upload_chunk(upload_id: str,request: Request):
    response = await file_service.upload_chunk(upload_id=upload_id,request=request)
    return response

@file_router.post("/merge/{upload_id}",dependencies = [Depends(verify_token)])
async def merge_chunks(upload_id: str):
    response = await file_service.merge_chunks(upload_id)
    return response

@file_router.get("/download/{filename}",dependencies = [Depends(verify_token)])
async def download_file(filename: str, request: Request):
    return await file_service.download_file(filename, request)

@file_router.get("/status/{upload_id}",dependencies = [Depends(verify_token)])
async def check_upload_status(upload_id: str):
    return await file_service.get_upload_status(upload_id)
