"""
Comparison history and review queue routes for ShipCheck.
"""
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from api.db import get_session
from api.models import ComparisonRecord, EmailRecord, utc_now
from api.schemas import ComparisonRecordRead, ComparisonField, ComparisonReviewUpdate
from api.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comparisons", tags=["Comparison History"])


def _to_read_model(rec: ComparisonRecord) -> ComparisonRecordRead:
    """Parses JSON string into ComparisonField list for read response."""
    try:
        raw_list = json.loads(rec.fields_json) if rec.fields_json else []
        fields = [ComparisonField(**item) for item in raw_list]
    except Exception as e:
        logger.error(f"Error parsing fields_json for comparison {rec.id}: {e}")
        fields = []

    return ComparisonRecordRead(
        id=rec.id,
        user_id=rec.user_id,
        email_id=rec.email_id,
        si_name=rec.si_name,
        bl_name=rec.bl_name,
        status=rec.status,
        summary=rec.summary,
        fields=fields,
        reviewed=rec.reviewed,
        reviewed_by=rec.reviewed_by,
        created_at=rec.created_at,
    )


@router.get("", response_model=List[ComparisonRecordRead], summary="List comparison history")
async def list_comparisons(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    email_id: Optional[str] = Query(default=None, description="Filter by linked email ID"),
    status: Optional[str] = Query(default=None, description="Filter by comparison status"),
    reviewed: Optional[bool] = Query(default=None, description="Filter by review status"),
    user_id: Optional[str] = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> List[ComparisonRecordRead]:
    """
    Returns historical SI vs BL comparison reports for the History / Reports page and human review queue.
    """
    stmt = select(ComparisonRecord)
    if user_id:
        stmt = stmt.where(ComparisonRecord.user_id == user_id)
    if email_id:
        stmt = stmt.where(ComparisonRecord.email_id == email_id)
    if status:
        stmt = stmt.where(ComparisonRecord.status == status)
    if reviewed is not None:
        stmt = stmt.where(ComparisonRecord.reviewed == reviewed)

    stmt = stmt.order_by(ComparisonRecord.created_at.desc()).offset(offset).limit(limit)
    records = session.exec(stmt).all()
    return [_to_read_model(r) for r in records]


@router.get("/{comparison_id}", response_model=ComparisonRecordRead, summary="Get single comparison report")
async def get_comparison(
    comparison_id: int,
    session: Session = Depends(get_session),
) -> ComparisonRecordRead:
    """Retrieves a single historical comparison report by ID."""
    rec = session.get(ComparisonRecord, comparison_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison report #{comparison_id} not found.",
        )
    return _to_read_model(rec)


@router.patch("/{comparison_id}/review", response_model=ComparisonRecordRead, summary="Mark comparison as reviewed")
async def review_comparison(
    comparison_id: int,
    payload: ComparisonReviewUpdate,
    session: Session = Depends(get_session),
) -> ComparisonRecordRead:
    """Updates the human review status on a comparison record."""
    rec = session.get(ComparisonRecord, comparison_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison report #{comparison_id} not found.",
        )

    rec.reviewed = payload.reviewed
    if payload.reviewed_by is not None:
        rec.reviewed_by = payload.reviewed_by
    if payload.status is not None:
        rec.status = payload.status

    session.add(rec)
    session.commit()
    session.refresh(rec)

    if payload.status is not None and rec.email_id:
        email_rec = session.get(EmailRecord, rec.email_id)
        if email_rec:
            email_rec.status = payload.status
            email_rec.updated_at = utc_now()
            session.add(email_rec)
            session.commit()

    return _to_read_model(rec)

