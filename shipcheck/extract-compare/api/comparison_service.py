"""
Shared comparison orchestration used by both the manual file-upload endpoint
(/api/compare) and the attachment-list endpoints (/api/compare/email,
/api/emails/eml) — anywhere we have a bag of (filename, raw_bytes) attachments
and need to figure out which is the SI, which is the BL, extract, compare, and
persist a ComparisonRecord.
"""
import json
import logging
from typing import List, Optional, Tuple

from sqlmodel import Session

from api.models import ComparisonRecord, EmailRecord, utc_now
from api.schemas import CompareResponse
from api.adapter import build_compare_response
from core.check_email import AttachmentExtractor, identify_si_bl
from core.compare_ai import DocumentComparator
from core.extract import FIELDS
from core.readers.reader import UnreadableAttachment

logger = logging.getLogger(__name__)

extractor = AttachmentExtractor()
comparator = DocumentComparator()


def save_comparison_record(
    session: Session,
    si_name: str,
    bl_name: str,
    response: CompareResponse,
    email_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> int:
    """Persists ComparisonRecord and updates the linked EmailRecord status, if any."""
    fields_data = [f.model_dump() for f in response.fields]
    fields_json = json.dumps(fields_data)

    rec = ComparisonRecord(
        user_id=user_id,
        email_id=email_id,
        si_name=si_name,
        bl_name=bl_name,
        status=response.status,
        summary=response.summary,
        fields_json=fields_json,
        reviewed=False,
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)

    if email_id:
        email_rec = session.get(EmailRecord, email_id)
        if email_rec:
            email_rec.status = response.status
            email_rec.updated_at = utc_now()
            session.add(email_rec)
            session.commit()

    return rec.id


def run_comparison_for_attachments(
    session: Session,
    attachments: List[Tuple[str, bytes]],
    email_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> CompareResponse:
    """
    Given an email's raw attachments, identifies the SI and BL among them,
    extracts and compares their fields, and saves a ComparisonRecord.
    Falls back to a "Needs Review" response (rather than raising) when the
    attachments can't be confidently resolved into an SI/BL pair.
    """
    usable = [(name, raw) for name, raw in attachments if raw]

    def _needs_review(reason: str, si_name: str = "unknown", bl_name: str = "unknown") -> CompareResponse:
        res = build_compare_response(
            si_fields={},
            bl_fields={},
            comparison=comparator.compare({}, {}, FIELDS),
            review_reason=reason,
        )
        res.comparison_id = save_comparison_record(session, si_name, bl_name, res, email_id, user_id)
        return res

    if len(usable) < 2:
        return _needs_review(f"Fewer than 2 usable attachments found ({len(usable)})")

    identified = identify_si_bl(usable, extractor)
    if identified is None:
        return _needs_review("Could not confidently identify an SI and a BL among the attachments")

    si, bl = identified
    if "error" in si or "error" in bl:
        broken = si if "error" in si else bl
        return _needs_review(f"Unreadable attachment: {broken['error']}", si["filename"], bl["filename"])

    comparison = comparator.compare(si["fields"], bl["fields"], FIELDS)
    res = build_compare_response(si["fields"], bl["fields"], comparison)
    res.comparison_id = save_comparison_record(session, si["filename"], bl["filename"], res, email_id, user_id)
    return res
