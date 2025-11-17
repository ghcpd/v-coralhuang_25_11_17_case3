# _*_ coding: utf-8 _*_
"""
Token parsing and validation utilities.
"""

import logging
from typing import Optional

from error import Unauthorized

logger = logging.getLogger(__name__)


def parse_bearer_token(auth_header: Optional[str]) -> int:
    """
    Parse user_id from Bearer token in Authorization header.
    
    Strict validation:
    - Header must be present
    - Format must be "Bearer <user_id>"
    - user_id must be a valid positive integer
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        user_id as integer
        
    Raises:
        Unauthorized: If header is invalid or malformed
    """
    if not auth_header:
        raise Unauthorized(msg="missing authorization header")
    
    # Strip whitespace
    auth_header = auth_header.strip()
    
    # Split into parts
    parts = auth_header.split()
    
    # Expect exactly 2 parts: "Bearer" and token
    if len(parts) != 2:
        raise Unauthorized(
            msg="invalid authorization header format, expected 'Bearer <user_id>'"
        )
    
    scheme, token = parts
    
    # Check scheme is Bearer
    if scheme.lower() != "bearer":
        raise Unauthorized(
            msg=f"invalid authorization scheme '{scheme}', expected 'Bearer'"
        )
    
    # Parse token as integer
    try:
        user_id = int(token)
    except ValueError:
        raise Unauthorized(
            msg=f"invalid token format, expected integer user_id, got '{token}'"
        )
    
    # Validate positive
    if user_id <= 0:
        raise Unauthorized(
            msg="user_id must be a positive integer"
        )
    
    return user_id
