from dataclasses import dataclass
from typing import Any, Dict


class APIException(Exception):
    status_code = 500
    error_code = 1000
    msg = "internal server error"

    def __init__(self, msg: str | None = None, error_code: int | None = None):
        if msg:
            self.msg = msg
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.msg)

    def to_payload(self, request_url: str) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "msg": self.msg,
            "request_url": request_url,
        }


class BadRequestError(APIException):
    status_code = 400
    error_code = 1001
    msg = "bad request"


class UnauthorizedError(APIException):
    status_code = 401
    error_code = 1002
    msg = "unauthorized"


class NotFoundError(APIException):
    status_code = 404
    error_code = 1003
    msg = "not found"


class ServerError(APIException):
    status_code = 500
    error_code = 1000
    msg = "internal error"


def success_payload(data: Any | None = None, msg: str = "ok") -> Dict[str, Any]:
    return {"error_code": 0, "msg": msg, "data": data or {}}
