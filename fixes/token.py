from fixes.error import Unauthorized
import re

def parse_token(auth_header: str) -> int:
    if not auth_header:
        raise Unauthorized("missing authorization header")
    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise Unauthorized("invalid authorization header format")
    token = parts[1]
    # Token must be digits only for this test env
    if not re.fullmatch(r"\d+", token):
        raise Unauthorized("invalid token content")
    return int(token)
