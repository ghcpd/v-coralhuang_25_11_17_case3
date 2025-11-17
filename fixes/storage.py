from uuid import uuid4
from urllib.parse import urljoin

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from fixes.errors import BadRequestError


class StorageBackend:
    def __init__(self, base_url: str):
        normalized = base_url.rstrip("/") + "/"
        self.base_url = normalized

    def upload(self, file_storage: FileStorage) -> str:
        filename = secure_filename(file_storage.filename or "")
        if not filename:
            raise BadRequestError(msg="uploaded file must include a filename")
        unique_path = f"{uuid4().hex}/{filename}"
        return urljoin(self.base_url, unique_path)
