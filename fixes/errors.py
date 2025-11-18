"""Error and response primitives for the fixed module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from flask import Response, current_app, jsonify, request


def success_response(data: Dict[str, Any], *, msg: str = "ok", error_code: int = 0) -> Response:
    """Return a standard success payload."""
    return jsonify({"error_code": error_code, "msg": msg, "data": data})


@dataclass
class ApiError(Exception):
    status_code: int
    error_code: int
    message: str

    def to_response(self) -> Response:
        payload = {
            "error_code": self.error_code,
            "msg": self.message,
            "request_url": request.path,
        }
        return jsonify(payload), self.status_code


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=401, error_code=40100, message=message)


class NotFoundError(ApiError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, error_code=40400, message=message)


class ValidationError(ApiError):
    def __init__(self, message: str = "Invalid request"):
        super().__init__(status_code=400, error_code=40000, message=message)


class ConflictError(ApiError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(status_code=409, error_code=40900, message=message)


class ServerError(ApiError):
    def __init__(self, message: str = "Server error"):
        super().__init__(status_code=500, error_code=50000, message=message)


def register_error_handlers(app) -> None:
    """Attach JSON error handlers to the Flask application."""

    @app.errorhandler(ApiError)
    def _handle_api_error(error: ApiError):
        current_app.logger.warning("API error: %s", error)
        return error.to_response()

    @app.errorhandler(Exception)
    def _handle_unexpected(error: Exception):
        current_app.logger.exception("Unhandled error: %s", error)
        payload = {
            "error_code": 50000,
            "msg": "internal server error",
            "request_url": request.path,
        }
        return jsonify(payload), 500

