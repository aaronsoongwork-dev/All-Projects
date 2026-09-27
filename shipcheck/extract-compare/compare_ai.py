"""Root shim re-exporting compare_ai components from core package."""
from core.compare_ai import *  # noqa: F401, F403
from core.compare_ai import (  # noqa: F401
    DocumentComparator,
    ComparisonResult,
    FieldComparison,
    ValueNormalizer,
    normalize,
    compare_fields_hybrid,
    compare_text_fields_ai,
)