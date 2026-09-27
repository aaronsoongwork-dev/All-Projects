"""
Core shipping document processing engine.
Provides classification, attachment extraction, and field comparison capabilities.
"""
from core.classifier import EmailClassifier, ClassificationResult
from core.compare_ai import (
    DocumentComparator,
    ComparisonResult,
    FieldComparison,
    ValueNormalizer,
    normalize,
    compare_fields_hybrid,
)
from core.extract import (
    extract_fields,
    extract_fields_from_image,
    FIELDS,
)
from core.check_email import (
    EmailMessage,
    AttachmentExtractor,
    EmailVerificationPipeline,
    VerificationReport,
    ConsoleReporter,
    EmailCheckerApp,
)
from core.parse_eml import parse_eml
from core.classify_wrapper import classify_email

__all__ = [
    "EmailClassifier",
    "ClassificationResult",
    "DocumentComparator",
    "ComparisonResult",
    "FieldComparison",
    "ValueNormalizer",
    "normalize",
    "compare_fields_hybrid",
    "extract_fields",
    "extract_fields_from_image",
    "FIELDS",
    "EmailMessage",
    "AttachmentExtractor",
    "EmailVerificationPipeline",
    "VerificationReport",
    "ConsoleReporter",
    "EmailCheckerApp",
    "parse_eml",
    "classify_email",
]

