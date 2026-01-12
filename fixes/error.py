# _*_ coding: utf-8 _*_
"""
Custom exception and response models for the application.
"""

from dataclasses import dataclass, asdict
from typing import Any, Optional, Dict


@dataclass
class ErrorResponse:
    """Standard error response structure."""
    error_code: int
    msg: str
    request_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return self.to_dict()


@dataclass
class SuccessResponse:
    """Standard success response structure."""
    error_code: int = 0
    msg: str = "success"
    data: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_code": self.error_code,
            "msg": self.msg,
            "data": self.data
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return self.to_dict()


class APIException(Exception):
    """Base API exception."""

    def __init__(self, code: int = 500, msg: str = "internal error", 
                 request_url: Optional[str] = None):
        """Initialize exception with error code and message."""
        self.code = code
        self.msg = msg
        self.request_url = request_url
        super().__init__(self.msg)

    def to_response(self) -> ErrorResponse:
        """Convert exception to error response."""
        return ErrorResponse(
            error_code=self.code,
            msg=self.msg,
            request_url=self.request_url
        )


class NotFound(APIException):
    """404 Not Found exception."""

    def __init__(self, msg: str = "not found", request_url: Optional[str] = None):
        super().__init__(code=404, msg=msg, request_url=request_url)


class BadRequest(APIException):
    """400 Bad Request exception."""

    def __init__(self, msg: str = "bad request", request_url: Optional[str] = None):
        super().__init__(code=400, msg=msg, request_url=request_url)


class Unauthorized(APIException):
    """401 Unauthorized exception."""

    def __init__(self, msg: str = "unauthorized", request_url: Optional[str] = None):
        super().__init__(code=401, msg=msg, request_url=request_url)


class Forbidden(APIException):
    """403 Forbidden exception."""

    def __init__(self, msg: str = "forbidden", request_url: Optional[str] = None):
        super().__init__(code=403, msg=msg, request_url=request_url)


class ServerError(APIException):
    """500 Internal Server Error exception."""

    def __init__(self, msg: str = "internal error", request_url: Optional[str] = None):
        super().__init__(code=500, msg=msg, request_url=request_url)


class Success(SuccessResponse):
    """Success response (for compatibility with original code)."""
    pass
