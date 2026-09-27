"""
Server-side Supabase client, using the SERVICE ROLE key (never expose this to
the browser). FastAPI is the only thing allowed to write final results —
this keeps report integrity out of the client's hands.
"""
from datetime import datetime, timezone

from supabase import Client, create_client

from config import SUPABASE_ENABLED, SUPABASE_SECRET_KEY, SUPABASE_URL

_client: Client | None = None


def is_enabled() -> bool:
    """
    False when no Supabase credentials are configured. The API still serves
    predictions in that state — it just can't persist or list them, so every
    write below no-ops and reads come back empty rather than crashing. This
    keeps the app usable for local development before the project is set up.
    """
    return SUPABASE_ENABLED


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client


def save_session_report(user_id: str, report: dict) -> dict:
    """
    Insert a completed session's fused emotion report.
    Expected `emotion_reports` table columns:
        id (uuid, pk, default gen_random_uuid())
        user_id (uuid, fk -> auth.users)
        created_at (timestamptz, default now())
        data (jsonb)
    """
    if not is_enabled():
        return {}

    client = get_client()
    result = (
        client.table("emotion_reports")
        .insert(
            {
                "user_id": user_id,
                "data": report,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    return result.data[0] if result.data else {}


def upload_audio_file(user_id: str, filename: str, file_bytes: bytes) -> str:
    """
    Uploads raw audio to a Supabase Storage bucket named 'audio-uploads'.
    Returns the storage path, or "" when persistence is disabled.
    Create the bucket in the Supabase dashboard first.
    """
    if not is_enabled():
        return ""

    client = get_client()
    path = f"{user_id}/{datetime.now(timezone.utc).timestamp()}_{filename}"
    client.storage.from_("audio-uploads").upload(
        path, file_bytes, {"content-type": "audio/wav"}
    )
    return path


def get_user_reports(user_id: str, limit: int = 50) -> list[dict]:
    if not is_enabled():
        return []

    client = get_client()
    result = (
        client.table("emotion_reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def delete_user_reports(user_id: str, report_ids: list[str]) -> int:
    """
    Delete the given reports, but only rows owned by this user — the
    user_id filter is what keeps one user from deleting another's data.
    Returns the number of rows deleted. No-op when persistence is off.
    """
    if not is_enabled() or not report_ids:
        return 0

    client = get_client()
    result = (
        client.table("emotion_reports")
        .delete()
        .eq("user_id", user_id)
        .in_("id", report_ids)
        .execute()
    )
    return len(result.data or [])
