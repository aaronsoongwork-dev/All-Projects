"""
AI-assisted comparison for shipping document fields.

Encapsulates deterministic comparison with an AI second-pass for text fields
(shipper, consignee, notify_party, port_of_loading, port_of_discharge) to
prevent false mismatches caused by superficial formatting differences, while
preserving strict deterministic checking for numeric fields.
"""
from dataclasses import dataclass, field
from typing import Any

import anthropic

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

DEFAULT_TEXT_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
]

DEFAULT_COMPARE_TOOL = {
    "name": "compare_field_values",
    "description": "Judge whether each pair of field values refers to the same real-world entity or place.",
    "input_schema": {
        "type": "object",
        "properties": {
            "comparisons": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "same": {
                            "type": "boolean",
                            "description": "true only if both values refer to the same real-world entity/place, allowing for formatting differences (separators, line breaks, word order, abbreviations, punctuation).",
                        },
                        "reasoning": {"type": "string"},
                    },
                    "required": ["field", "same", "reasoning"],
                },
            },
        },
        "required": ["comparisons"],
    },
}

DEFAULT_SYSTEM_PROMPT = """You judge whether two extracted field values refer to the same \
real-world company or place, despite superficial formatting differences \
between two source documents (different separators like "|" vs newlines, \
different address component order, abbreviations vs full names, minor \
punctuation differences).

Mark "same": true only when you are confident they refer to the identical \
entity or place — formatting differences alone should not cause a "false" \
verdict.

Mark "same": false whenever the actual identity differs — a different \
company name, a different city, a different country — even if the values \
share a superficial similarity like a matching code, abbreviation, or \
partial text overlap. A shared code or abbreviation does NOT override an \
actual difference in the named entity. When genuinely uncertain, prefer \
"same": false — a real system should escalate rather than silently forgive \
a possible defect."""


class ValueNormalizer:
    """Normalizes field values for uniform string comparison."""

    def __init__(self, separators: list[str] | None = None):
        self.separators = separators or ["|", ";", "\n"]

    def normalize(self, value: Any) -> str | None:
        """Strip whitespace, uppercase, and unify separators."""
        if value is None:
            return None
        text = str(value).strip().upper()
        for sep in self.separators:
            text = text.replace(sep, ",")
        text = text.replace(",", " ")
        return " ".join(text.split())


@dataclass
class FieldComparison:
    """Comparison breakdown for an individual field."""
    field_name: str
    si_value: Any
    bl_value: Any
    is_match: bool
    ai_evaluated: bool = False
    ai_reasoning: str | None = None


@dataclass
class ComparisonResult:
    """Aggregate result of comparing two shipping documents."""
    defect_fields: list[str] = field(default_factory=list)
    ai_reasoning: dict[str, str] = field(default_factory=dict)
    field_comparisons: dict[str, FieldComparison] = field(default_factory=dict)

    @property
    def is_match(self) -> bool:
        return len(self.defect_fields) == 0

    @property
    def has_defect(self) -> bool:
        return bool(self.defect_fields)

    def to_tuple(self) -> tuple[list[str], dict[str, str]]:
        """Backwards-compatible unpacker returning (defect_fields, ai_reasoning)."""
        return self.defect_fields, self.ai_reasoning


class DocumentComparator:
    """
    Compares extracted fields between Shipping Instructions (SI) and Bills of Lading (BL).
    Applies deterministic checks first, escalating disagreeing text fields to Claude Haiku.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        client: anthropic.Anthropic | None = None,
        text_fields: list[str] | None = None,
        normalizer: ValueNormalizer | None = None,
        compare_tool: dict | None = None,
        system_prompt: str | None = None,
    ):
        self.model = model
        self.client = client
        self.text_fields = set(text_fields if text_fields is not None else DEFAULT_TEXT_FIELDS)
        self.normalizer = normalizer or ValueNormalizer()
        self.compare_tool = compare_tool or DEFAULT_COMPARE_TOOL
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def _get_client(self) -> anthropic.Anthropic:
        return self.client or anthropic.Anthropic()

    def normalize(self, value: Any) -> str | None:
        """Normalize a field value using the configured normalizer."""
        return self.normalizer.normalize(value)

    def compare_text_fields_ai(
        self,
        si_fields: dict,
        bl_fields: dict,
        fields_to_check: list[str],
    ) -> dict[str, dict]:
        """
        Uses Claude to evaluate whether differing text representations refer to the same real-world entity.
        Returns {field: {"same": bool, "reasoning": str}}.
        """
        if not fields_to_check:
            return {}

        client = self._get_client()

        pairs_text = "\n\n".join(
            f"Field: {f}\nSI value: {si_fields.get(f)!r}\nBL value: {bl_fields.get(f)!r}"
            for f in fields_to_check
        )

        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            tools=[self.compare_tool],
            tool_choice={"type": "tool", "name": "compare_field_values"},
            messages=[{"role": "user", "content": f"Compare these field value pairs:\n\n{pairs_text}"}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "compare_field_values":
                return {
                    c["field"]: {"same": c["same"], "reasoning": c["reasoning"]}
                    for c in block.input.get("comparisons", [])
                }

        raise RuntimeError("Claude did not return the expected tool call")

    def compare(
        self,
        si_fields: dict,
        bl_fields: dict,
        all_fields: list[str] | None = None,
    ) -> ComparisonResult:
        """
        Executes hybrid comparison on the given field dictionaries.
        Deterministic check runs first; text fields that differ are evaluated by AI.
        """
        if all_fields is None:
            all_fields = list(dict.fromkeys(list(si_fields.keys()) + list(bl_fields.keys())))

        defect_fields: list[str] = []
        disagreeing_text_fields: list[str] = []
        field_comparisons: dict[str, FieldComparison] = {}

        # 1. Deterministic pass
        for field in all_fields:
            si_raw = si_fields.get(field)
            bl_raw = bl_fields.get(field)
            si_norm = self.normalize(si_raw)
            bl_norm = self.normalize(bl_raw)

            if si_norm == bl_norm:
                field_comparisons[field] = FieldComparison(
                    field_name=field,
                    si_value=si_raw,
                    bl_value=bl_raw,
                    is_match=True,
                )
            else:
                if field in self.text_fields:
                    disagreeing_text_fields.append(field)
                else:
                    # Numeric fields: trust deterministic result immediately
                    defect_fields.append(field)
                    field_comparisons[field] = FieldComparison(
                        field_name=field,
                        si_value=si_raw,
                        bl_value=bl_raw,
                        is_match=False,
                    )

        # 2. AI second pass for disagreeing text fields
        ai_reasoning: dict[str, str] = {}
        if disagreeing_text_fields:
            ai_results = self.compare_text_fields_ai(si_fields, bl_fields, disagreeing_text_fields)
            for field in disagreeing_text_fields:
                si_raw = si_fields.get(field)
                bl_raw = bl_fields.get(field)
                result = ai_results.get(
                    field,
                    {"same": False, "reasoning": "AI comparison did not return a verdict"}
                )
                reasoning = result.get("reasoning", "")
                is_same = result.get("same", False)

                ai_reasoning[field] = reasoning
                field_comparisons[field] = FieldComparison(
                    field_name=field,
                    si_value=si_raw,
                    bl_value=bl_raw,
                    is_match=is_same,
                    ai_evaluated=True,
                    ai_reasoning=reasoning,
                )

                if not is_same:
                    defect_fields.append(field)

        return ComparisonResult(
            defect_fields=defect_fields,
            ai_reasoning=ai_reasoning,
            field_comparisons=field_comparisons,
        )


# --- Module-level backward-compatible wrappers ---

_default_comparator = DocumentComparator()


def normalize(value: Any) -> str | None:
    """Backward-compatible function delegating to ValueNormalizer."""
    return _default_comparator.normalize(value)


def compare_text_fields_ai(
    si_fields: dict,
    bl_fields: dict,
    fields_to_check: list[str],
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Backward-compatible function delegating to DocumentComparator."""
    comparator = DocumentComparator(client=client) if client else _default_comparator
    return comparator.compare_text_fields_ai(si_fields, bl_fields, fields_to_check)


def compare_fields_hybrid(
    si_fields: dict,
    bl_fields: dict,
    all_fields: list[str],
    client: anthropic.Anthropic | None = None,
) -> tuple[list[str], dict]:
    """Backward-compatible function returning (defect_fields, ai_reasoning)."""
    comparator = DocumentComparator(client=client) if client else _default_comparator
    result = comparator.compare(si_fields, bl_fields, all_fields)
    return result.to_tuple()