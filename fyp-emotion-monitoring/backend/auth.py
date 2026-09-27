"""
Verifies Supabase-issued JWTs via Supabase's JWKS endpoint. Supabase now
signs new tokens with an asymmetric key (ES256) by default — the old
single-shared-secret (HS256) approach is being phased out project by
project. This fetches Supabase's public verification keys directly, so
it keeps working through any future key rotation with no code changes.

Dev mode: with DISABLE_AUTH=true every caller is accepted and treated as
DEV_USER_ID. That exists purely so the frontend can be built against a real
running model before the team has Supabase credentials — main.py prints a
warning at startup whenever it's on.
"""
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from storage import get_client  # reuse the existing service-role client
from config import DEV_USER_ID, DISABLE_AUTH, SUPABASE_URL

security = HTTPBearer(auto_error=False)

# Cached client — PyJWKClient handles its own key caching internally, so
# this is safe to reuse across requests instead of re-fetching every time.
_jwks_client: PyJWKClient | None = None

# Cache MFA-enrollment lookups briefly — avoids hitting Supabase's admin
# API on every single request, while still catching enrollment changes
# within a reasonable window.
_mfa_cache: dict[str, tuple[bool, float]] = {}
_MFA_CACHE_TTL = 60  # seconds

def _get_jwks_client() -> PyJWKClient | None:
    global _jwks_client
    if not SUPABASE_URL:
        return None
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def _dev_user() -> dict:
    return {"sub": DEV_USER_ID, "email": "dev@localhost", "dev_mode": True}


def decode_jwt(token: str) -> dict | None:
    """Returns the decoded payload if valid, else None."""
    client = _get_jwks_client()
    if client is None:
        return None
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],  # covers old + new
            audience="authenticated",
        )
        return payload
    except jwt.InvalidTokenError:
        return None

def _user_has_verified_mfa(user_id: str) -> bool:
    now = time.time()
    cached = _mfa_cache.get(user_id)
    if cached and now - cached[1] < _MFA_CACHE_TTL:
        return cached[0]

    try:
        client = get_client()
        result = client.auth.admin.get_user_by_id(user_id)
        factors = result.user.factors or []
        has_verified = any(f.status == "verified" for f in factors)
    except Exception as e:
        # Fail closed on the safety-relevant side: if we can't confirm
        # MFA status, don't silently let an aal1 token through for a
        # user who might have MFA enabled.
        print(f"[warn] MFA lookup failed for {user_id}: {e}")
        has_verified = True  # forces rejection below — safer default

    _mfa_cache[user_id] = (has_verified, now)
    return has_verified


def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if DISABLE_AUTH:
        return _dev_user()

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    payload = decode_jwt(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    aal = payload.get("aal")
    if aal == "aal1" and _user_has_verified_mfa(payload.get("sub", "")):
        raise HTTPException(
            status_code=401,
            detail="MFA verification required to complete this session",
        )

    return payload


def verify_ws_token(token: str) -> dict | None:
    if DISABLE_AUTH:
        return _dev_user()
    return decode_jwt(token)