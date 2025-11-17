from fixes.errors import UnauthorizedError


def parse_user_id(auth_header: str | None, prefix: str, claim_prefix: str) -> int:
    if not auth_header:
        raise UnauthorizedError(msg="missing authorization header")
    parts = auth_header.strip().split()
    if len(parts) != 2:
        raise UnauthorizedError(msg="authorization header must include scheme and credentials")
    scheme, token = parts
    if scheme != prefix:
        raise UnauthorizedError(msg=f"authorization scheme must be {prefix}")
    if not token.startswith(claim_prefix):
        raise UnauthorizedError(msg="token format is invalid")
    user_id = token[len(claim_prefix) :]
    if not user_id.isdigit():
        raise UnauthorizedError(msg="token does not contain a valid user id")
    return int(user_id)
