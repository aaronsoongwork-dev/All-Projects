"""
Adapter layer mapping between internal domain entities and frontend contracts.
"""
from typing import Dict, Any, List, Optional
from api.schemas import (
    EmailType,
    EmailStatus,
    ComparisonField,
    CompareResponse,
    EmailClassifyResponse,
)
from core.classifier import ClassificationResult
from core.compare_ai import ComparisonResult

# Maps backend categories to frontend EmailType
CATEGORY_MAP: Dict[str, EmailType] = {
    "BL_COMPARISON": "Document Comparison",
    "SI_REQUEST": "New SI Request",
    "INVOICE_QUERY": "Invoice Query",
    "GENERAL": "General",
    "SPAM": "Spam",
}

# Maps frontend EmailType to backend categories
REVERSE_CATEGORY_MAP: Dict[EmailType, str] = {
    v: k for k, v in CATEGORY_MAP.items()
}

# Maps internal 7 field keys to frontend display labels
FIELD_DISPLAY_LABELS: Dict[str, str] = {
    "shipper": "Shipper",
    "consignee": "Consignee",
    "notify_party": "Notify Party",
    "port_of_loading": "Port of Loading",
    "port_of_discharge": "Port of Discharge",
    "container_count": "Container Count",
    "gross_weight_kg": "Gross Weight (kg)",
}

ORDERED_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
]


def map_category_to_email_type(category: str) -> EmailType:
    """Translates backend category string to frontend EmailType literal."""
    norm = category.strip().upper()
    if norm in CATEGORY_MAP:
        return CATEGORY_MAP[norm]
    # Fuzzy fallback if needed
    for k, v in CATEGORY_MAP.items():
        if k in norm:
            return v
    return "General"


def build_classify_response(result: ClassificationResult) -> EmailClassifyResponse:
    """Builds an EmailClassifyResponse from a domain ClassificationResult."""
    email_type = map_category_to_email_type(result.category)
    confidence = result.confidence if result.confidence is not None else 1.0

    reasoning_parts = []
    if result.probabilities:
        top_probs = sorted(result.probabilities.items(), key=lambda x: x[1], reverse=True)[:3]
        prob_str = ", ".join(f"{k}: {p:.2f}" for k, p in top_probs)
        reasoning_parts.append(f"Model: {prob_str}")

    reasoning = "; ".join(reasoning_parts) if reasoning_parts else None

    return EmailClassifyResponse(
        type=email_type,
        confidence=confidence,
        reasoning=reasoning,
    )


def build_compare_response(
    si_fields: Dict[str, Any],
    bl_fields: Dict[str, Any],
    comparison: ComparisonResult,
    review_reason: Optional[str] = None,
) -> CompareResponse:
    """Translates field dictionaries and ComparisonResult into CompareResponse."""
    if review_reason:
        status: EmailStatus = "Needs Review"
    elif comparison.has_defect:
        status = "Mismatch"
    else:
        status = "Match"

    fields: List[ComparisonField] = []
    for f_key in ORDERED_FIELDS:
        display_label = FIELD_DISPLAY_LABELS.get(f_key, f_key)
        si_val = si_fields.get(f_key)
        bl_val = bl_fields.get(f_key)

        si_str = str(si_val) if si_val is not None else "—"
        bl_str = str(bl_val) if bl_val is not None else "—"

        comp = comparison.field_comparisons.get(f_key)
        is_match = comp.is_match if comp else (si_val == bl_val and si_val is not None)

        fields.append(
            ComparisonField(
                field=display_label,
                si=si_str,
                bl=bl_str,
                match=is_match,
            )
        )

    # Build human readable summary
    summary_parts = []
    if status == "Match":
        summary_parts.append("All 7 fields match across SI and draft BL.")
    elif status == "Mismatch":
        mismatched_labels = [
            FIELD_DISPLAY_LABELS.get(f, f) for f in comparison.defect_fields
        ]
        summary_parts.append(f"Discrepancies found in {len(comparison.defect_fields)} field(s): {', '.join(mismatched_labels)}.")
        for f, note in comparison.ai_reasoning.items():
            summary_parts.append(f"[{FIELD_DISPLAY_LABELS.get(f, f)}]: {note}")
    else:
        summary_parts.append(f"Document comparison flagged for manual review ({review_reason or 'unknown reason'}).")

    return CompareResponse(
        status=status,
        fields=fields,
        summary=" ".join(summary_parts),
    )

