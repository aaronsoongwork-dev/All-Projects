"""
Stage 2 — Extract, using the Claude API.

Given raw document text (already pulled out of txt/pdf/docx/xlsx by the
readers/ module), ask Claude to pull out the 7 standard shipping fields,
using tool-use so the response is guaranteed valid structured JSON rather
than free text we'd have to parse ourselves.

The prompt explicitly tells the model: (a) field labels vary between
documents ("Load Port" vs "Port of Loading"), match by MEANING not exact
wording, and (b) if a value genuinely isn't present, return null rather
than guessing.
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
VISION_MODEL = "claude-sonnet-5"

FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
]

EXTRACT_TOOL = {
    "name": "extract_shipping_fields",
    "description": "Record the 7 standard shipping fields found in a shipping document (SI or BL).",
    "input_schema": {
        "type": "object",
        "properties": {
            "shipper": {
                "type": ["string", "null"],
                "description": "The FULL text block for the shipper/exporter field — company name AND any address lines that appear directly under or after that label, as one string. Always include the address if the document has one; never return name-only if an address is present.",
            },
            "consignee": {
                "type": ["string", "null"],
                "description": "The FULL text block for the consignee field (may appear as 'Consignee', 'To the Order of', etc.) — company name AND any address lines directly under or after that label, as one string. Always include the address if the document has one; never return name-only if an address is present.",
            },
            "notify_party": {
                "type": ["string", "null"],
                "description": "The FULL text block for the notify party field (may appear as 'Notify' or 'Notify Party') — company name AND any address lines directly under or after that label, as one string. Always include the address if the document has one; never return name-only if an address is present.",
            },
            "port_of_loading": {
                "type": ["string", "null"],
                "description": "Port of loading / load port (may appear as 'POL', 'Load Port', 'Port of Loading').",
            },
            "port_of_discharge": {
                "type": ["string", "null"],
                "description": "Port of discharge (may appear as 'POD', 'Port of Discharge').",
            },
            "container_count": {
                "type": ["string", "null"],
                "description": "Total container count, e.g. \"6 x 40'HC\". Use the TOTAL, not a per-container line item.",
            },
            "gross_weight_kg": {
                "type": ["number", "null"],
                "description": "TOTAL gross weight in kilograms as a plain number, no commas/units. Use the TOTAL if the document also lists per-container weights.",
            },
        },
        "required": FIELDS,
    },
}

SYSTEM_PROMPT = """You extract structured data from shipping documents (Shipping \
Instructions or draft Bills of Lading). Documents differ in layout and label \
wording between companies — e.g. "Port of Loading", "POL", and "Load Port" all \
mean the same field. Match fields by MEANING, not exact label text.

If a field is genuinely not present anywhere in the document, is blank, or \
contains a placeholder like 'TBA', 'TBD', 'N/A', or underscores, return null \
for it. Do not guess, fabricate, or return '<UNKNOWN>' as a string value. When \
a total is available alongside per-item breakdowns (e.g. total gross weight vs \
per-container weight), use the TOTAL.

For shipper, consignee, and notify_party: always extract the FULL text block \
under that label, including any address lines, as one string. Be consistent \
about this even across different documents for the same shipment — do not \
sometimes include the address and sometimes omit it."""


def _run_extraction(content, model: str = MODEL, client: anthropic.Anthropic | None = None) -> dict:
    """Shared call + parse logic for both text and image extraction."""
    client = client or anthropic.Anthropic()

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_shipping_fields"},
        messages=[{"role": "user", "content": content}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_shipping_fields":
            result = block.input
            return {field: result.get(field) for field in FIELDS}

    raise RuntimeError("Claude did not return the expected tool call")


def extract_fields(document_text: str, client: anthropic.Anthropic | None = None) -> dict:
    content = f"Extract the 7 fields from this document:\n\n{document_text}"
    return _run_extraction(content, model=MODEL, client=client)


def extract_fields_from_image(
    image_bytes: bytes, media_type: str = "image/png", client: anthropic.Anthropic | None = None
) -> dict:
    """Same extraction, but from a rendered document image instead of text —
    used as the fallback for scanned PDFs with no text layer. Uses a
    stronger model than plain-text extraction (see VISION_MODEL comment)."""
    import base64

    image_b64 = base64.standard_b64encode(image_bytes).decode()
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_b64},
        },
        {
            "type": "text",
            "text": "Extract the 7 fields from this shipping document image. Read carefully — this is a scanned document, take extra care not to misread similar-looking characters or company names.",
        },
    ]
    return _run_extraction(content, model=VISION_MODEL, client=client)


if __name__ == "__main__":
    # quick manual test run with:  ANTHROPIC_API_KEY=sk-... python extract.py
    sample = """
    SHIPPING INSTRUCTION
    Shipper: APRIL FAR EAST (M) SDN BHD
    Consignee (Non-Negotiable): EAST BRIGHT FZ-LLC
    Notify: EAST BRIGHT FZ-LLC
    Port of Loading (POL): NANTONG, CHINA (CNNTG)
    POD: KARACHI, PAKISTAN (PKKHI)
    Total Containers: 6 x 40'HC
    Gross Wt (kgs): 131,058 KG
    """
    print(extract_fields(sample))
