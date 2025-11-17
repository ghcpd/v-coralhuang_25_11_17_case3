from flask import jsonify, request


class APIException(Exception):
    def __init__(self, code=500, msg="internal error", status_code=500):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.status_code = status_code

    def to_response(self):
        return jsonify({
            "error_code": self.code,
            "msg": self.msg,
            "request_url": request.path,
        }), self.status_code


class NotFound(APIException):
    def __init__(self, msg="not found"):
        super().__init__(code=404, msg=msg, status_code=404)


class Unauthorized(APIException):
    def __init__(self, msg="unauthorized"):
        super().__init__(code=401, msg=msg, status_code=401)


class BadRequest(APIException):
    def __init__(self, msg="bad request"):
        super().__init__(code=400, msg=msg, status_code=400)


class ServerError(APIException):
    def __init__(self, msg="internal error"):
        super().__init__(code=500, msg=msg, status_code=500)


# Structured success helper
class Success:
    def __init__(self, data=None, error_code=0, msg="ok"):
        self.data = data if data is not None else {}
        self.msg = msg
        self.error_code = error_code

    def to_response(self):
        return jsonify({
            "error_code": self.error_code,
            "msg": self.msg,
            "data": self.data,
        }), 200
