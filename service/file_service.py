import os
import shutil
import struct
import uuid
import re

from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse

from utils.upload_tracker import UploadTracker
import logging

BASE_DIR = "storage"
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
CHUNKS_DIR = os.path.join(BASE_DIR, "chunks")
COMPLETED_DIR = os.path.join(BASE_DIR, "completed")
CHUNK_HEADER_SIZE = struct.calcsize(">II B")

tracker = UploadTracker()

class FileService:


    async def initialize_upload(self,filename: str):
        try:
            upload_id = f"{uuid.uuid4().hex}_{filename}"
            os.makedirs(os.path.join(CHUNKS_DIR, upload_id), exist_ok=True)
            logging.info(f"[INIT] Initialized upload: {upload_id}")
            return {"upload_id": upload_id}
        except Exception as e:
            logging.exception("[INIT] Failed to initialize upload")
            raise HTTPException(status_code=500, detail="Failed to initialize upload")


    async def upload_chunk(self,upload_id: str,request: Request):
        try:
            data = await request.body()

            if len(data) <= CHUNK_HEADER_SIZE:
                logging.warning(f"[UPLOAD] Chunk too small for {upload_id}")
                raise HTTPException(status_code=400, detail="Invalid chunk: too small")

            try:
                start, end, checksum = struct.unpack(">II B", data[:CHUNK_HEADER_SIZE])
            except struct.error:
                logging.warning(f"[UPLOAD] Header unpacking failed for {upload_id}")
                raise HTTPException(status_code=400, detail="Invalid header")

            content = data[CHUNK_HEADER_SIZE:]
            calculated_checksum = sum(content) % 256

            if checksum != calculated_checksum:
                logging.warning(f"[UPLOAD] Checksum mismatch for chunk {start}-{end} in {upload_id}")
                raise HTTPException(status_code=400, detail="Checksum mismatch")

            if tracker.is_uploaded(upload_id, start):
                logging.info(f"[UPLOAD] Duplicate chunk {start}-{end} for {upload_id}")
                return {"message": "Chunk already received"}

            chunk_path = os.path.join(CHUNKS_DIR, upload_id, f"{start}.part")
            with open(chunk_path, "wb") as f:
                f.write(content)

            tracker.mark_uploaded(upload_id, start)
            logging.info(f"[UPLOAD] Received chunk {start}-{end} for {upload_id}")
            return {"message": "Chunk uploaded"}

        except HTTPException:
            raise
        except Exception as e:
            logging.exception(f"[UPLOAD] Failed to upload chunk for {upload_id}")
            raise HTTPException(status_code=500, detail="Upload error")

    async def merge_chunks(self,upload_id: str):
        chunk_folder = os.path.join(CHUNKS_DIR, upload_id)
        if not os.path.isdir(chunk_folder):
            logging.warning(f"[MERGE] Upload ID not found: {upload_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload ID not found")

        try:
            _, filename = upload_id.split("_", 1)
        except ValueError:
            logging.warning(f"[MERGE] Invalid upload ID: {upload_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid upload ID")

        output_path = os.path.join(COMPLETED_DIR, filename)
        if os.path.exists(output_path):
            logging.warning(f"[MERGE] File already assembled: {filename}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File already assembled")

        uploaded_chunks = tracker.get_uploaded_chunks(upload_id)
        if not uploaded_chunks:
            logging.warning(f"[MERGE] No chunks found for {upload_id}")
            raise HTTPException(status_code=400, detail="No chunks found")

        try:
            with open(output_path, "wb") as out:
                for start in uploaded_chunks:
                    chunk_path = os.path.join(chunk_folder, f"{start}.part")
                    if not os.path.exists(chunk_path):
                        logging.warning(f"[MERGE] Missing chunk at {start} for {upload_id}")
                        raise HTTPException(status_code=400, detail=f"Missing chunk at {start}")
                    with open(chunk_path, "rb") as f:
                        out.write(f.read())

            tracker.clear(upload_id)
            shutil.rmtree(chunk_folder, ignore_errors=True)
            logging.info(f"[MERGE] Upload {upload_id} assembled successfully")
            return {"message": "Upload completed", "file": filename}
        except HTTPException:
            raise
        except Exception as e:
            logging.exception(f"[MERGE] Error during merge for {upload_id}")
            raise HTTPException(status_code=500, detail="Merge failed")

    async def download_file(self, filename: str, request: Request):
        file_path = os.path.join(COMPLETED_DIR, filename)

        if not os.path.exists(file_path):
            logging.warning(f"[DOWNLOAD] File not found: {filename}")
            raise HTTPException(status_code=404, detail="File not found")

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get("range")

        def file_stream(start: int, end: int):
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(4096, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
                    remaining -= len(data)

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1

                if start >= file_size or end >= file_size:
                    logging.warning(f"[DOWNLOAD] Invalid range {start}-{end} for {filename}")
                    raise HTTPException(status_code=416, detail="Requested range not satisfiable")

                content_length = end - start + 1
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                    "Content-Type": "application/octet-stream",
                }
                logging.info(f"[DOWNLOAD] Sending range {start}-{end} of {filename}")
                return StreamingResponse(file_stream(start, end), status_code=206, headers=headers)

        # Full file download
        headers = {
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Content-Type": "application/octet-stream",
        }
        logging.info(f"[DOWNLOAD] Sending full file: {filename}")
        return StreamingResponse(file_stream(0, file_size - 1), headers=headers)


    async def get_upload_status(self, upload_id: str):
        try:
            # Extract original filename
            try:
                _, filename = upload_id.split("_", 1)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid upload ID")

            completed_file_path = os.path.join(COMPLETED_DIR, filename)
            chunk_folder = os.path.join(CHUNKS_DIR, upload_id)

            if os.path.exists(completed_file_path):
                return {"status": "complete", "filename": filename}

            elif os.path.exists(chunk_folder):
                uploaded_chunks = tracker.get_uploaded_chunks(upload_id)
                return {
                    "status": "partial",
                    "received_chunks": uploaded_chunks,
                    "chunk_count": len(uploaded_chunks)
                }

            else:
                return {"status": "pending", "message": "No chunks received yet"}

        except Exception as e:
            logging.exception(f"[STATUS] Failed to check status for {upload_id}")
            raise HTTPException(status_code=500, detail="Failed to retrieve status")
