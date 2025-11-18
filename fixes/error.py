from flask import jsonify

class APIError(Exception):
    def __init__(self, error_code: int, msg: str, status_code: int = 400):
        self.error_code = error_code
        self.msg = msg
        self.status_code = status_code

    def to_response(self, request_url=None):
        body = {
            "error_code": self.error_code,
            "msg": self.msg,
        }
        if request_url:
            body["request_url"] = request_url
        return jsonify(body), self.status_code

class NotFound(APIError):
    def __init__(self, msg="not found"):
        super().__init__(404, msg, 404)

class Unauthorized(APIError):
    def __init__(self, msg="unauthorized"):
        super().__init__(401, msg, 401)

class ServerError(APIError):
    def __init__(self, msg="internal error"):
        super().__init__(500, msg, 500)

class Success:
    def __init__(self, data=None, error_code=0, msg="success"):
        self.data = data or {}
        self.error_code = error_code
        self.msg = msg

    def to_response(self):
        return jsonify({"error_code": self.error_code, "msg": self.msg, "data": self.data})
