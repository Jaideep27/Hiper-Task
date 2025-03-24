import logging
import os
import shutil
import struct

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from auth.jwt import create_access_token
from auth import jwt
from routes.file_routes import file_router

# Directories
BASE_DIR = "storage"
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
CHUNKS_DIR = os.path.join(BASE_DIR, "chunks")
COMPLETED_DIR = os.path.join(BASE_DIR, "completed")

# Ensure directories exist and empty them
for d in [UPLOADS_DIR, CHUNKS_DIR, COMPLETED_DIR]:
    if os.path.exists(d):
        for filename in os.listdir(d):
            file_path = os.path.join(d, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    else:
        os.makedirs(d, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Header size: 4 + 4 + 1 bytes
CHUNK_HEADER_SIZE = struct.calcsize(">II B")

# FastAPI app
app = FastAPI()
app.include_router(file_router)



@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != "secret":
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}