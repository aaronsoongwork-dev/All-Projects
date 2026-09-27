"""
Document comparison endpoint router.
Supports file uploads (PDF/DOCX/TXT/XLSX), direct text payloads, and
attachment lists auto-identified as SI/BL (for the inbox auto-compare flow).
Persists comparison history in SQLite ComparisonRecord table.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlmodel import Session
from api.db import get_session
from api.schemas import CompareResponse, CompareTextRequest
from api.adapter import build_compare_response
from api.comparison_service import (
    extractor as _extractor,
    comparator as _comparator,
    save_comparison_record as _save_comparison_record,
    run_comparison_for_attachments,
)
from core.extract import extract_fields, FIELDS
from core.readers.reader import UnreadableAttachment

from api.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Comparison"])


@router.post("/compare", response_model=CompareResponse, summary="Compare SI vs BL uploaded document files")
async def compare_documents_files(
    si_file: UploadFile = File(..., description="Shipping Instruction document (PDF, TXT, DOCX, XLSX)"),
    bl_file: UploadFile = File(..., description="Draft Bill of Lading document (PDF, TXT, DOCX, XLSX)"),
    email_id: Optional[str] = Form(default=None, description="Optional Gmail ID to link this comparison"),
    user_id: Optional[str] = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> CompareResponse:
    """
    Extracts the 7 shipping fields from uploaded SI and draft BL documents and compares them.
    Saves the result to ComparisonRecord and returns comparison_id.
    """
    try:
        si_bytes = await si_file.read()
        bl_bytes = await bl_file.read()

        if not si_bytes or not bl_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or both uploaded files are empty.",
            )

        si_name = si_file.filename or "si_document"
        bl_name = bl_file.filename or "bl_document"

        try:
            si_fields, _ = _extractor.extract_from_bytes(si_name, si_bytes)
            bl_fields, _ = _extractor.extract_from_bytes(bl_name, bl_bytes)
        except UnreadableAttachment as e:
            res = build_compare_response(
                si_fields={},
                bl_fields={},
                comparison=_comparator.compare({}, {}, FIELDS),
                review_reason=f"Unreadable attachment: {str(e)}",
            )
            res.comparison_id = _save_comparison_record(session, si_name, bl_name, res, email_id, user_id)
            return res

        comparison = _comparator.compare(si_fields, bl_fields, FIELDS)
        res = build_compare_response(si_fields, bl_fields, comparison)
        res.comparison_id = _save_comparison_record(session, si_name, bl_name, res, email_id, user_id)
        return res

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during document comparison: {e}", exc_info=True)
        err_str = str(e)
        if "Could not resolve authentication method" in err_str or "ANTHROPIC_API_KEY" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ANTHROPIC_API_KEY is not configured on the backend server.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {err_str}",
        )


@router.post("/compare/text", response_model=CompareResponse, summary="Compare raw document texts")
async def compare_documents_text(
    payload: CompareTextRequest,
    user_id: Optional[str] = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> CompareResponse:
    """
    Extracts the 7 shipping fields from raw SI and BL document texts and compares them.
    Saves the result to ComparisonRecord and returns comparison_id.
    """
    try:
        si_fields = extract_fields(payload.si_text)
        bl_fields = extract_fields(payload.bl_text)

        comparison = _comparator.compare(si_fields, bl_fields, FIELDS)
        res = build_compare_response(si_fields, bl_fields, comparison)
        res.comparison_id = _save_comparison_record(
            session, "raw_si_text", "raw_bl_text", res, payload.email_id, user_id
        )
        return res
    except Exception as e:
        err_str = str(e)
        if "Could not resolve authentication method" in err_str or "ANTHROPIC_API_KEY" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ANTHROPIC_API_KEY is not configured on the backend server.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text comparison failed: {err_str}",
        )


@router.post("/compare/email", response_model=CompareResponse, summary="Auto-compare an email's attachments")
async def compare_email_attachments(
    email_id: str = Form(..., description="Gmail message ID (or EML-derived ID) to link this comparison to"),
    attachments: List[UploadFile] = File(default_factory=list, description="All attachments found on the email"),
    user_id: Optional[str] = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> CompareResponse:
    """
    Identifies the SI and BL among an email's attachments, extracts and
    compares their fields, and saves the result linked to email_id. Falls
    back to a "Needs Review" result (not an error) when the attachments
    can't be confidently resolved into an SI/BL pair.
    """
    try:
        files = [(f.filename or "attachment", await f.read()) for f in attachments]
        return run_comparison_for_attachments(session, files, email_id, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email attachment comparison: {e}", exc_info=True)
        err_str = str(e)
        if "Could not resolve authentication method" in err_str or "ANTHROPIC_API_KEY" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ANTHROPIC_API_KEY is not configured on the backend server.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email attachment comparison failed: {err_str}",
        )
