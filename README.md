

# File Handling REST API

A robust and secure API built using **FastAPI** to manage file transfers between remote devices and a server. This API ensures **reliable uploads, secure downloads, resumable file transfers, and real-time status monitoring**.

## 📂 Project Structure

```
.
├── .git/                 # Git repository metadata
├── .idea/                # IDE-specific settings (if using PyCharm)
├── .pytest_cache/        # pytest cache files
├── .venv/                # Virtual environment (if using a virtual environment)
├── __pycache__/          # Compiled Python files
├── auth/                 # Authentication-related modules
│   ├── jwt.py            # JWT token handling
├── routes/               # API route handlers
│   ├── file_routes.py    # Routes for file uploads and processing
├── service/              # Business logic and services
│   ├── file_service.py   # File processing logic
├── storage/              # Directory for storing uploaded files
├── temp/                 # Temporary file storage
├── tests/                # Unit tests
│   ├── test_upload.py    # Tests for file upload functionality
├── utils/                # Utility functions
├── .gitignore            # Git ignore rules
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── test_sample.txt       # Sample test data file

```

----------

## 📌 Features

✅ **Chunk-Based File Uploads**: Supports sending files in pieces and reassembling them.  
✅ **Resumable Uploads**: If interrupted, uploads can resume from the last received byte.  
✅ **Partial Downloads**: Supports range-based downloads for large files.  
✅ **Real-Time File Status Monitoring**: Tracks whether files are fully received, partially received, or pending.  
✅ **Automatic Cleanup**: Periodically removes stale or incomplete file chunks.  
✅ **Security**: JWT-based authentication to restrict access.

----------

## 🏗️ Tech Stack

-   **FastAPI** (Python) - High-performance web framework
-   **Uvicorn** - ASGI server for FastAPI
-   **JWT Authentication** - Secure token-based authentication
-   **AsyncIO** - Handles I/O operations efficiently
-   **SQLite / Cloud Storage Support** - Stores metadata and file information

----------

## 🚀 API Endpoints

### 🔹 Authentication
| Method | Endpoint       | Description                      |
|--------|--------------|----------------------------------|
| POST   | `/auth/token` | Generate JWT for authentication |

### 🔹 File Upload
| Method | Endpoint            | Description                        |
|--------|---------------------|------------------------------------|
| POST   | `/upload/start`     | Initiate an upload session        |
| POST   | `/upload/chunk`     | Upload a file chunk (with validation) |
| POST   | `/upload/complete`  | Mark file upload as complete      |

### 🔹 File Download
| Method | Endpoint                     | Description                                   |
|--------|------------------------------|-----------------------------------------------|
| GET    | `/download/{filename}`       | Download a file                              |
| GET    | `/download/partial/{filename}` | Partial file download (Content-Range support) |

### 🔹 File Status
| Method | Endpoint               | Description                     |
|--------|------------------------|---------------------------------|
| GET    | `/status/{filename}`   | Check file transfer status     |

### 🔹 Background Cleanup
| Method  | Endpoint     | Description                                  |
|---------|------------|----------------------------------------------|
| DELETE  | `/cleanup` | Remove old or incomplete file uploads       |


----------

## 🛠️ Setup Instructions

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt

```

### 2️⃣ Run the API Server

```bash
uvicorn main:app --port 8000

```

### 3️⃣ Run Tests

```bash
pytest tests/test_upload.py -vv

```

### 4️⃣ API Authentication (JWT)

-   Generate a JWT token via `/auth/token`
-   Pass `Authorization: Bearer <TOKEN>` in API requests

----------

## ⚡ Example Usage

### 🔹 Upload a File in Chunks

1.  Start an upload session:
    
    ```json
    POST /upload/start  
    { "filename": "largefile.zip", "size": 100000000 }
    
    ```
    
2.  Upload chunks:
    
    ```json
    POST /upload/chunk  
    { "filename": "largefile.zip", "chunk_index": 1, "data": "<binary_data>" }
    
    ```
    
3.  Complete the upload:
    
    ```json
    POST /upload/complete  
    { "filename": "largefile.zip" }
    
    ```
    

### 🔹 Download a File Partially

```http
GET /download/partial/largefile.zip  
Range: bytes=1000-2000

```

----------

## 🔒 Security

-   Uses **JWT Authentication** for secured access
-   Validates file chunks with **checksum validation**
-   Implements **background cleanup** for better resource management

----------

## 📜 License

This project is licensed under the MIT License.

----------
