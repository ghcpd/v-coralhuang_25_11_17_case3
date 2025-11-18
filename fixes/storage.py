"""Offline-friendly storage helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def simulate_avatar_upload(
    file_storage: FileStorage, *, user_id: int, bucket_url: str, storage_dir: str
) -> str:
    """
    Persist the uploaded avatar locally and return a fake CDN URL.

    The function never performs network I/O and is deterministic so tests can
    make assertions about the generated URL.
    """
    filename = secure_filename(file_storage.filename or "avatar.bin")
    if not filename:
        filename = "avatar.bin"

    data = file_storage.read()
    if not data:
        raise ValueError("empty file")

    digest = hashlib.sha256(data).hexdigest()
    suffix = Path(filename).suffix or ".bin"
    stored_name = f"user_{user_id}_{digest[:12]}{suffix}"

    target_path = Path(storage_dir) / stored_name
    target_path.write_bytes(data)

    # Reset stream for potential downstream consumers.
    file_storage.stream.seek(0)

    return f"{bucket_url}/{stored_name}"

