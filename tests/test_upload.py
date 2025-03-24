import os
import struct
import uuid

import requests

BASE_URL = "http://localhost:8000"
CHUNK_SIZE = 1024 * 1024  # 1 MB

def get_token():
    res = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "secret"})
    assert res.status_code == 200
    return res.json()["access_token"]

def create_test_file(path: str, size_mb: int):
    content = b"This is a test file.\n" * 64  # ~1KB
    with open(path, "wb") as f:
        for _ in range(size_mb * 1024):  # 5 MB
            f.write(content)


def create_header(start: int, end: int, data: bytes) -> bytes:
    checksum = sum(data) % 256
    return struct.pack(">II B", start, end, checksum)

def check_status(upload_id: str, expected_status: str):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(f"{BASE_URL}/status/{upload_id}",headers=headers)
    assert res.status_code == 200, f"Status check failed: {res.text}"
    status_data = res.json()
    assert status_data["status"] == expected_status, f"Expected '{expected_status}', got '{status_data['status']}'"
    print(f"[STATUS] Upload {upload_id}: {status_data['status']} - Received chunks: {status_data.get('received_chunks', [])}")


def upload_file(file_path: str):
    filename = os.path.basename(file_path)
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.post(f"{BASE_URL}/init", params={"filename": filename}, headers=headers)
    assert res.status_code == 200
    upload_id = res.json()["upload_id"]

    # 1. Check initial status: partial
    check_status(upload_id, "partial")

    with open(file_path, "rb") as f:
        start = 0
        chunk_count = 0
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            end = start + len(data) - 1
            header = create_header(start, end, data)
            chunk = header + data

            r = requests.post(f"{BASE_URL}/upload/{upload_id}", data=chunk,headers=headers)
            assert r.status_code == 200, f"Chunk upload failed: {r.text}"
            print(f"Uploaded chunk {start}-{end}")
            start = end + 1

            # 2. After first chunk, check status: partial
            if chunk_count == 0:
                check_status(upload_id, "partial")
            chunk_count += 1

    # 3. Merge uploaded chunks
    res = requests.post(f"{BASE_URL}/merge/{upload_id}",headers=headers)
    assert res.status_code == 200
    print(f"File merged: {res.json()}")

    # 4. Final status check: complete
    check_status(upload_id, "complete")


def test_upload_file_flow():
    os.makedirs("temp", exist_ok=True)
    test_file_path = f"test_sample.txt"
    create_test_file(test_file_path, size_mb=5)
    upload_file(test_file_path)



def test_full_download():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    FILENAME = "test_sample.txt"
    url = f"{BASE_URL}/download/{FILENAME}"
    response = requests.get(url,headers=headers)
    assert response.status_code == 200
    assert "Accept-Ranges" in response.headers
    print(f"[OK] Full file downloaded: {len(response.content)} bytes")


def test_partial_download():
    token = get_token()
    FILENAME = "test_sample.txt"

    # Request bytes 7 to 18 -> "this is a te"
    headers = {"Authorization": f"Bearer {token}",
               "Range": "bytes=7-18"
               }
    response = requests.get(f"{BASE_URL}/download/{FILENAME}", headers=headers)

    assert response.status_code == 206
    assert "content-range" in response.headers