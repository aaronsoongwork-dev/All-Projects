"""
Classification endpoint router.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.db import get_session
from api.models import EmailRecord, utc_now
from api.schemas import EmailClassifyRequest, EmailClassifyResponse
from api.adapter import build_classify_response, map_category_to_email_type
from core.classifier import EmailClassifier

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Classification"])
_classifier = EmailClassifier()


def classify_text_heuristic(subject: str, snippet: str, body: str) -> str:
    """Fallback keyword classification when API key is missing."""
    text = f"{subject} {snippet} {body}".lower()
    if any(w in text for w in ["bill of lading", "b/l", "bl draft", "confirm bl", "si and bl"]):
        return "BL_COMPARISON"
    elif "invoice" in text or "remittance" in text or "payment" in text:
        return "INVOICE_QUERY"
    elif "shipping instruction" in text:
        return "SI_REQUEST"
    elif any(w in text for w in ["unsubscribe", "gift card", "promotion", "claim your"]):
        return "SPAM"
    else:
        return "GENERAL"


@router.post("/classify", response_model=EmailClassifyResponse, summary="Classify inbound email")
async def classify_email_endpoint(
    payload: EmailClassifyRequest,
    session: Session = Depends(get_session),
) -> EmailClassifyResponse:
    """
    Classifies an email's intent (Document Comparison, New SI Request, Invoice Query, General, Spam).
    If payload.id is provided, upserts the classification into EmailRecord.
    """
    email_data = {
        "subject": payload.subject,
        "snippet": payload.snippet,
        "body": payload.body,
    }

    try:
        try:
            domain_result = _classifier.classify(email_data)
            response = build_classify_response(domain_result)
        except ValueError as e:
            logger.warning(f"Classification configuration notice: {e}")
            cat = classify_text_heuristic(payload.subject, payload.snippet, payload.body)
            response = EmailClassifyResponse(
                type=map_category_to_email_type(cat),
                confidence=0.85,
                reasoning=f"Heuristic fallback (API key not configured: {e})",
            )

        # Upsert into SQLite if an email ID is provided
        if payload.id:
            record = session.get(EmailRecord, payload.id)
            if record:
                record.email_type = response.type
                record.confidence = response.confidence
                record.reasoning = response.reasoning
                record.updated_at = utc_now()
                session.add(record)
                session.commit()
            else:
                # Create basic record
                initial_status = "New" if response.type == "Document Comparison" else "Classified"
                record = EmailRecord(
                    id=payload.id,
                    thread_id=payload.id,
                    from_name="Unknown",
                    from_email="unknown@example.com",
                    subject=payload.subject,
                    snippet=payload.snippet,
                    date_str="Today",
                    timestamp=int(utc_now().timestamp() * 1000),
                    email_type=response.type,
                    status=initial_status,
                    confidence=response.confidence,
                    reasoning=response.reasoning,
                    body_snippet=payload.body[:200] if payload.body else payload.snippet[:200],
                )
                session.add(record)
                session.commit()

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email classification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )
