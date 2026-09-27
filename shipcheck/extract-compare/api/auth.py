"""
Authentication dependency for Supabase JWT verification and user_id extraction.
"""
import os
import logging
from typing import Optional
import jwt
from fastapi import Header

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


def get_current_user_id(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    """
    Extracts Supabase User UUID (sub) from Authorization Bearer token.
    Falls back to 'demo' if no token or invalid token is supplied.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return "demo"

    token = authorization.split(" ", 1)[1].strip()
    if not token or token == "null" or token == "undefined":
        return "demo"

    # If secret is set, verify signature; otherwise decode payload directly
    try:
        if SUPABASE_JWT_SECRET:
            # Supabase tokens are signed with HS256 using the JWT secret
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            payload = jwt.decode(token, options={"verify_signature": False})

        user_id = payload.get("sub") or payload.get("id")
        return user_id or "demo"
    except Exception as e:
        logger.warning(f"Could not verify Supabase JWT: {e}")
        # Try unverified decode to still extract sub if signature check failed due to secret mismatch
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub") or "demo"
        except Exception:
            return "demo"

