"""
Auth routes for syncing users with Supabase auth.users and generating Supabase-compatible JWTs.
"""
import os
import time
import json
import uuid
import logging
from typing import Optional
import jwt
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from api.db import engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


class UserSyncRequest(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str = "google"


class UserSyncResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    token: str


@router.post("/sync-user", response_model=UserSyncResponse)
def sync_user(req: UserSyncRequest):
    """
    Ensures user exists in Supabase auth.users and returns a signed Supabase JWT.
    """
    if not req.email:
        raise HTTPException(status_code=400, detail="Email is required")

    email = req.email.strip().lower()
    name = req.name or email.split("@")[0]

    try:
        with engine.connect() as conn:
            # Check if user already exists in auth.users
            res = conn.execute(
                text("SELECT id FROM auth.users WHERE lower(email) = :email"),
                {"email": email}
            ).fetchone()

            if res:
                user_id = str(res[0])
                # Ensure identity also exists for existing user if missing
                try:
                    ident_exists = conn.execute(
                        text("SELECT id FROM auth.identities WHERE user_id = :uid"),
                        {"uid": user_id}
                    ).fetchone()
                    if not ident_exists:
                        ident_dict = {"sub": user_id, "email": email, "full_name": name}
                        if req.picture:
                            ident_dict["avatar_url"] = req.picture
                        conn.execute(
                            text("""
                                INSERT INTO auth.identities (
                                    id, provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at
                                ) VALUES (
                                    :id, :pid, :uid, :data, :provider, NOW(), NOW(), NOW()
                                )
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "pid": user_id,
                                "uid": user_id,
                                "data": json.dumps(ident_dict),
                                "provider": req.provider or "google",
                            }
                        )
                        conn.commit()
                except Exception as ident_err:
                    logger.warning(f"Failed to verify/link identity for existing user {email}: {ident_err}")
            else:
                user_id = str(uuid.uuid4())
                meta = json.dumps({"full_name": name, "avatar_url": req.picture or ""})
                provider = req.provider or "google"
                app_meta = json.dumps({"provider": provider, "providers": [provider]})
                conn.execute(
                    text("""
                        INSERT INTO auth.users (
                            id, aud, role, email, email_confirmed_at,
                            raw_user_meta_data, raw_app_meta_data, created_at, updated_at
                        ) VALUES (
                            :id, 'authenticated', 'authenticated', :email, NOW(),
                            :meta, :app_meta, NOW(), NOW()
                        )
                    """),
                    {
                        "id": user_id,
                        "email": email,
                        "meta": meta,
                        "app_meta": app_meta,
                    }
                )
                conn.commit()

                # Also link identity so user shows up with correct provider in Supabase Dashboard
                try:
                    ident_dict = {"sub": user_id, "email": email, "full_name": name}
                    if req.picture:
                        ident_dict["avatar_url"] = req.picture
                    conn.execute(
                        text("""
                            INSERT INTO auth.identities (
                                id, provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at
                            ) VALUES (
                                :id, :pid, :uid, :data, :provider, NOW(), NOW(), NOW()
                            )
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "pid": user_id,
                            "uid": user_id,
                            "data": json.dumps(ident_dict),
                            "provider": provider,
                        }
                    )
                    conn.commit()
                except Exception as ident_err:
                    logger.warning(f"Failed to link identity for {email}: {ident_err}")

                logger.info(f"Created new user in Supabase auth.users: {email} ({user_id})")

        # Generate signed Supabase JWT
        payload = {
            "sub": user_id,
            "email": email,
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 60 * 60 * 24 * 30,  # 30 days
            "user_metadata": {"full_name": name, "avatar_url": req.picture or ""},
            "app_metadata": {"provider": req.provider, "providers": [req.provider]},
        }
        token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256") if SUPABASE_JWT_SECRET else jwt.encode(payload, "secret", algorithm="HS256")

        return UserSyncResponse(
            user_id=user_id,
            email=email,
            name=name,
            picture=req.picture,
            token=token,
        )
    except Exception as e:
        logger.error(f"Failed to sync user with Supabase auth: {e}")
        raise HTTPException(status_code=500, detail=f"User sync failed: {e}")

