"""
Batch runner — drop .eml files into the emails/ folder, run this, get a
report for each one.

Usage:
    python3 run_eml_folder.py             (defaults to ./emails)
    python3 run_eml_folder.py some/folder

Set ANTHROPIC_API_KEY before running.

Note on classify: this uses a placeholder heuristic (2+ attachments =>
BL_COMPARISON) until the real classify.py from the team repo is wired in
here. Swap classify_email() for the real one once it's ready.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "readers"))

from check_email import AttachmentExtractor
from classifier import EmailClassifier
from compare_ai import DocumentComparator, ValueNormalizer
from extract import FIELDS
from parse_eml import parse_eml
from readers.reader import UnreadableAttachment, read_attachment_text

DEFAULT_FOLDER = Path(__file__).parent / "emails"

classifier = EmailClassifier()
extractor = AttachmentExtractor()
normalizer = ValueNormalizer()
comparator = DocumentComparator()


def identify_si_bl(attachments: list[tuple[str, bytes]]) -> tuple[dict, dict] | None:
    """Given a list of (filename, raw_bytes) attachments, figure out which
    one is the SI and which is the BL by reading their content (real emails
    won't reliably have '_SI'/'_BL' in the filename the way the dataset
    does). Returns (si_info, bl_info) or None if it can't confidently tell,
    where each info dict has filename/fields/method.

    Detection: look for "SHIPPING INSTRUCTION" or "BILL OF LADING" near the
    top of the extracted text. Falls back to filename hints if content is
    ambiguous.
    """
    docs = []
    for filename, raw in attachments:
        try:
            fields, method = extractor.extract_from_bytes(filename, raw)
        except UnreadableAttachment as e:
            docs.append({"filename": filename, "error": str(e)})
            continue

        # re-extract raw text just for role-sniffing (cheap, already read once)
        try:
            text = read_attachment_text(filename, raw)
        except Exception:
            text = ""
        header = text[:300].upper()

        if "SHIPPING INSTRUCTION" in header or "_si." in filename.lower() or "_si_" in filename.lower():
            role = "SI"
        elif "BILL OF LADING" in header or "_bl." in filename.lower() or "_bl_" in filename.lower():
            role = "BL"
        else:
            role = None

        docs.append({"filename": filename, "fields": fields, "method": method, "role": role})

    identified = [d for d in docs if d.get("role") in ("SI", "BL")]
    si = next((d for d in identified if d["role"] == "SI"), None)
    bl = next((d for d in identified if d["role"] == "BL"), None)

    if si and bl:
        return si, bl
    return None  # couldn't confidently identify both roles


def process_one(eml_path: Path):
    print(f"\n{'=' * 70}")
    print(f"FILE: {eml_path.name}")
    print("=" * 70)

    raw = eml_path.read_bytes()
    parsed = parse_eml(raw)

    print(f"From:    {parsed['from']}")
    print(f"Subject: {parsed['subject']}")
    body_preview = parsed["body"][:150] + ("..." if len(parsed["body"]) > 150 else "")
    print(f"Body:    {body_preview}")

    parsed_for_classify = {**parsed, "attachments": [fn for fn, _ in parsed["attachments"]]}
    classification = classifier.classify(parsed_for_classify)
    print(f"\nCategory: {classification.category}")

    if not classification.is_bl_comparison:
        print("(not a comparison request — nothing further to do)")
        return

    if len(parsed["attachments"]) < 2:
        print("NEEDS_REVIEW: missing_attachment (fewer than 2 attachments)")
        return

    result = identify_si_bl(parsed["attachments"])
    if result is None:
        print("NEEDS_REVIEW: wrong_doc_type (couldn't confidently identify an SI and a BL)")
        for filename, raw in parsed["attachments"]:
            print(f"  - saw attachment: {filename}")
        return

    si, bl = result
    if "error" in si or "error" in bl:
        broken = si if "error" in si else bl
        print(f"NEEDS_REVIEW: unreadable ({broken['filename']}: {broken['error']})")
        return

    print(f"SI: {si['filename']} (read via {si['method']})")
    print(f"BL: {bl['filename']} (read via {bl['method']})")
    print()

    comparison = comparator.compare(si["fields"], bl["fields"], FIELDS)

    print(f"{'FIELD':<20} {'SI':<30} {'BL':<30} {'MATCH'}")
    print("-" * 90)
    for field in FIELDS:
        comp = comparison.field_comparisons.get(field)
        si_val = si["fields"].get(field)
        bl_val = bl["fields"].get(field)
        match = comp.is_match if comp else False
        marker = "OK" if match else "MISMATCH"
        print(f"{field:<20} {str(si_val)[:28]:<30} {str(bl_val)[:28]:<30} {marker}")
        if comp and comp.ai_reasoning:
            print(f"  (AI: {comp.ai_reasoning})")

    print()
    print("Result:", "MISMATCH" if comparison.has_defect else "OK — no mismatch detected")


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER
    eml_files = sorted(folder.glob("*.eml"))

    if not eml_files:
        print(f"No .eml files found in {folder}")
        return

    print(f"Found {len(eml_files)} .eml file(s) in {folder}")
    for path in eml_files:
        process_one(path)


if __name__ == "__main__":
    main()
