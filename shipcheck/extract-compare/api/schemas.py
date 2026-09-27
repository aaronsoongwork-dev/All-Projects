"""
Pydantic schemas directly matching the ShipCheck React frontend TypeScript contracts.
"""
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from api.models import EmailRecord

# Matches TypeScript union types from frontend
EmailType = Literal[
    "Document Comparison", "New SI Request", "Invoice Query", "General", "Spam"
]

EmailStatus = Literal[
    "New", "Mismatch", "Match", "Needs Review", "Classified", "Processing"
]


class EmailClassifyRequest(BaseModel):
    """Payload sent by the frontend to classify an email."""
    id: Optional[str] = Field(default=None, description="Optional Gmail message ID to persist classification")
    subject: str = Field(..., description="Email subject line")
    snippet: str = Field(default="", description="Short preview snippet of email")
    body: str = Field(default="", description="Full or partial email body")


class EmailClassifyResponse(BaseModel):
    """Response returned to the frontend with classification type and confidence."""
    type: EmailType
    confidence: float
    reasoning: Optional[str] = None


class ComparisonField(BaseModel):
    """Represents extraction and comparison for a single shipping field."""
    field: str = Field(..., description="Human-readable field name, e.g. 'Shipper'")
    si: str = Field(..., description="Extracted value from SI document or '—'")
    bl: str = Field(..., description="Extracted value from BL document or '—'")
    match: bool = Field(..., description="True if SI and BL match")


class CompareResponse(BaseModel):
    """Response returned to the frontend after document comparison."""
    status: EmailStatus  # "Match", "Mismatch", or "Needs Review"
    fields: List[ComparisonField]
    summary: Optional[str] = None
    comparison_id: Optional[int] = Field(default=None, description="ID of persisted ComparisonRecord")


class CompareTextRequest(BaseModel):
    """Direct text-based comparison payload."""
    si_text: str = Field(..., description="Raw text of Shipping Instruction")
    bl_text: str = Field(..., description="Raw text of Bill of Lading")
    email_id: Optional[str] = Field(default=None, description="Optional linked Gmail email ID")


class EmailRecordCreate(BaseModel):
    """Client payload representing an email fetched from Gmail."""
    id: str = Field(..., description="Gmail message ID")
    thread_id: str
    from_name: str
    from_email: str
    subject: str
    snippet: str
    date_str: str
    timestamp: int
    has_attachments: bool = False
    body: Optional[str] = None
    body_snippet: Optional[str] = None
    email_type: Optional[EmailType] = None
    status: Optional[EmailStatus] = None
    user_id: Optional[str] = None


class ComparisonRecordRead(BaseModel):
    """Read model for saved comparison history."""
    id: int
    user_id: Optional[str] = None
    email_id: Optional[str] = None
    si_name: str
    bl_name: str
    status: str
    summary: Optional[str] = None
    fields: List[ComparisonField]
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    created_at: datetime


class ComparisonReviewUpdate(BaseModel):
    """Payload to mark a comparison as reviewed, optionally overriding its status
    (e.g. a human resolving a "Needs Review" case to Match/Mismatch)."""
    reviewed: bool = True
    reviewed_by: Optional[str] = None
    status: Optional[EmailStatus] = None


class EmailSyncRequest(BaseModel):
    """Payload to trigger server-side sync with Gmail."""
    page_token: Optional[str] = Field(default=None, description="Optional Gmail pageToken for pagination")
    max_results: int = Field(default=25, ge=1, le=100)


class EmailSyncResponse(BaseModel):
    """Response returned after server-side Gmail sync."""
    emails: List[EmailRecord]
    next_page_token: Optional[str] = None
    synced_count: int
    new_records: int


class GoogleAuthCodeRequest(BaseModel):
    """Payload to exchange Google OAuth authorization code for server refresh token."""
    code: str = Field(..., description="Google OAuth authorization code")
    redirect_uri: Optional[str] = Field(default="postmessage", description="Redirect URI used during code request")


class EmailAttachmentsResponse(BaseModel):
    """Filenames of a Gmail message's attachments (no bytes)."""
    filenames: List[str]


class GmailIntegrationStatus(BaseModel):
    """Status of server-side Gmail integration. Deliberately never includes
    the raw access/refresh token - clients only need to know whether a
    connection exists, not the credential itself."""
    connected: bool
    account_email: Optional[str] = None
    last_sync_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check payload."""
    status: str
    version: str
    providers: Dict[str, bool]
