"""Strict Authorization token parsing utilities."""

from __future__ import annotations

import re
from typing import Tuple

from .errors import UnauthorizedError

BEARER_PREFIX = "Bearer"
TOKEN_PATTERN = re.compile(r"^user:(?P<user_id>[1-9][0-9]*)$")


def parse_authorization_header(value: str | None) -> Tuple[int, str]:
    """
    Extract the user ID from a token.

    Expected header: ``Bearer user:<id>`` where ``id`` is a positive integer.
    """
    if not value:
        raise UnauthorizedError("missing authorization header")

    parts = value.strip().split()
    if len(parts) != 2 or parts[0] != BEARER_PREFIX:
        raise UnauthorizedError("invalid authorization header format")

    match = TOKEN_PATTERN.match(parts[1])
    if not match:
        raise UnauthorizedError("invalid token payload")

    return int(match.group("user_id")), parts[1]

