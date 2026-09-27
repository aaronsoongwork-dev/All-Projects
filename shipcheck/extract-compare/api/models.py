"""
SQLModel database models for ShipCheck SQLite persistence.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EmailRecord(SQLModel, table=True):
    """Stores classified emails fetched from Gmail."""
    id: str = Field(primary_key=True)               # Gmail message ID (immutable)
    user_id: Optional[str] = Field(default=None, index=True) # Supabase User UUID
    thread_id: str
    from_name: str
    from_email: str
    subject: str
    snippet: str
    date_str: str
    timestamp: int = Field(sa_column=Column(BigInteger, nullable=False))
    email_type: str                                  # 'Document Comparison', 'New SI Request', 'Invoice Query', 'General', 'Spam'
    status: str                                      # 'Match', 'Mismatch', 'Needs Review', 'Classified', 'Processing', 'New'
    confidence: float = 1.0
    reasoning: Optional[str] = None
    has_attachments: bool = False
    body_snippet: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ComparisonRecord(SQLModel, table=True):
    """Stores SI vs draft BL comparison reports and history."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, index=True) # Supabase User UUID
    email_id: Optional[str] = Field(default=None, index=True)
    si_name: str
    bl_name: str
    status: str                                      # 'Match', 'Mismatch', 'Needs Review'
    summary: Optional[str] = None
    fields_json: str                                 # Serialized JSON string of List[ComparisonField]
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class EmailIntegration(SQLModel, table=True):
    """Stores shared Gmail integration tokens for server-side syncing."""
    id: str = Field(default="primary", primary_key=True)
    provider: str = Field(default="gmail")
    account_email: Optional[str] = None
    refresh_token: str
    access_token: Optional[str] = None
    access_token_expires_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    next_page_token: Optional[str] = None
    updated_at: datetime = Field(default_factory=utc_now)


