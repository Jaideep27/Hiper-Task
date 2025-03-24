import time
from typing import Dict, List
from threading import Lock

class UploadTracker:
    def __init__(self):
        self._uploads: Dict[str, List[int]] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = Lock()

    def mark_uploaded(self, upload_id: str, start: int):
        with self._lock:
            if upload_id not in self._uploads:
                self._uploads[upload_id] = []
            if start not in self._uploads[upload_id]:
                self._uploads[upload_id].append(start)
            self._timestamps[upload_id] = time.time()  # Update timestamp

    def is_uploaded(self, upload_id: str, start: int) -> bool:
        with self._lock:
            return start in self._uploads.get(upload_id, [])

    def get_uploaded_chunks(self, upload_id: str) -> List[int]:
        with self._lock:
            return sorted(self._uploads.get(upload_id, []))

    def clear(self, upload_id: str):
        with self._lock:
            self._uploads.pop(upload_id, None)
            self._timestamps.pop(upload_id, None)
