"""
Runs the full pipeline (classify -> extract -> compare -> escalate) across
every email in the dataset, and writes both submission.json (the required
scoring format) and an Excel report.

Expects inbox/ and attachments/ folders next to this script (same as
check_email.py). Needs a .env file with ANTHROPIC_API_KEY and
OPENROUTER_API_KEY, or both set as environment variables.

Usage:
    python3 run_full_dataset.py

Safe to interrupt and re-run — progress is checkpointed to
results_checkpoint.json after every 10 emails, and already-processed
emails are skipped on the next run. Delete that file to start fresh.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "readers"))

from dotenv import load_dotenv

load_dotenv()

import openpyxl

from check_email import AttachmentExtractor, EmailMessage
from classifier import EmailClassifier
from compare_ai import DocumentComparator
from extract import FIELDS
from readers.reader import UnreadableAttachment

INBOX_DIR = Path(__file__).parent / "inbox"
ATTACHMENTS_DIR = Path(__file__).parent / "attachments"
CHECKPOINT_PATH = Path(__file__).parent / "results_checkpoint.json"
EXCEL_PATH = Path(__file__).parent / "results.xlsx"

CHECKPOINT_EVERY = 10

classifier = EmailClassifier()
extractor = AttachmentExtractor(ATTACHMENTS_DIR)
comparator = DocumentComparator()


def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text())
    return {}


def save_checkpoint(results: dict):
    CHECKPOINT_PATH.write_text(json.dumps(results, indent=2))


def process_comparison(email_msg: EmailMessage) -> dict:
    attachments = email_msg.attachments

    if len(attachments) < 2:
        return {
            "status": "NEEDS_REVIEW", "review_reason": "missing_attachment",
            "has_defect": False, "defect_fields": [], "details": "",
        }

    si_path = email_msg.find_si_attachment()
    bl_path = email_msg.find_bl_attachment()
    if not si_path or not bl_path:
        return {
            "status": "NEEDS_REVIEW", "review_reason": "wrong_doc_type",
            "has_defect": False, "defect_fields": [], "details": "",
        }

    try:
        si_fields, _ = extractor.extract_from_file(si_path)
        bl_fields, _ = extractor.extract_from_file(bl_path)
    except UnreadableAttachment as e:
        return {
            "status": "NEEDS_REVIEW", "review_reason": "unreadable",
            "has_defect": False, "defect_fields": [], "details": str(e),
        }

    missing = [f for f in FIELDS if si_fields.get(f) is None or bl_fields.get(f) is None]
    if missing:
        return {
            "status": "NEEDS_REVIEW", "review_reason": "missing_value",
            "has_defect": False, "defect_fields": [],
            "details": f"could not extract: {missing}",
        }

    comparison = comparator.compare(si_fields, bl_fields, FIELDS)
    defect_fields = comparison.defect_fields
    ai_reasoning = comparison.ai_reasoning

    detail_parts = []
    for field in defect_fields:
        si_val, bl_val = si_fields.get(field), bl_fields.get(field)
        note = f"{field}: SI='{si_val}' vs BL='{bl_val}'"
        if field in ai_reasoning:
            note += f" (AI: {ai_reasoning[field]})"
        detail_parts.append(note)

    status = "MISMATCH" if defect_fields else "OK"
    return {
        "status": status, "review_reason": None,
        "has_defect": bool(defect_fields), "defect_fields": defect_fields,
        "details": "; ".join(detail_parts),
    }


def main():
    email_files = sorted(INBOX_DIR.glob("email_*.json"))
    results = load_checkpoint()
    total = len(email_files)
    print(f"Total emails: {total}, already processed: {len(results)}\n")

    processed_this_run = 0
    for i, path in enumerate(email_files, 1):
        email = json.loads(path.read_text())
        eid = email["email_id"]
        if eid in results:
            continue

        print(f"[{i}/{total}] {eid}...", end=" ", flush=True)
        email_msg = EmailMessage.from_dict(email)
        try:
            classification = classifier.classify(email_msg)
            category = classification.category
        except Exception as e:
            print(f"CLASSIFY ERROR: {e}")
            continue

        row = {
            "category": category, "status": "OK", "review_reason": None,
            "has_defect": False, "defect_fields": [], "details": "",
        }
        if classification.is_bl_comparison:
            try:
                row.update(process_comparison(email_msg))
            except Exception as e:
                row.update({
                    "status": "NEEDS_REVIEW", "review_reason": "unreadable",
                    "details": f"unexpected error: {e}",
                })

        results[eid] = row
        processed_this_run += 1
        print(row["category"], "-", row.get("status") or "")

        if processed_this_run % CHECKPOINT_EVERY == 0:
            save_checkpoint(results)
            print(f"  (checkpoint saved, {len(results)}/{total} done)")

    save_checkpoint(results)
    print(f"\nDone. {len(results)}/{total} emails processed.")
    write_excel(results, email_files)
    write_submission_json(results)


def write_submission_json(results: dict):
    """The exact schema the self-eval endpoint expects — no extra fields."""
    submission = {
        eid: {
            "category": r["category"],
            "status": r["status"],
            "review_reason": r["review_reason"],
            "has_defect": r["has_defect"],
            "defect_fields": r["defect_fields"],
        }
        for eid, r in results.items()
    }
    with open(Path(__file__).parent / "submission.json", "w") as f:
        json.dump(submission, f, indent=2)
    print(f"Wrote submission.json ({len(submission)} emails)")


def write_excel(results: dict, email_files: list):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    headers = ["email_id", "subject", "category", "status", "review_reason",
               "has_defect", "defect_fields", "mismatch_details"]
    ws.append(headers)

    for path in email_files:
        email = json.loads(path.read_text())
        eid = email["email_id"]
        r = results.get(eid, {})
        ws.append([
            eid,
            email.get("subject", ""),
            r.get("category", ""),
            r.get("status", ""),
            r.get("review_reason", ""),
            r.get("has_defect", False),
            ", ".join(r.get("defect_fields", [])),
            r.get("details", ""),
        ])

    for col in ws.columns:
        max_len = max(len(str(c.value)) for c in col if c.value is not None)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    wb.save(EXCEL_PATH)
    print(f"Wrote {EXCEL_PATH}")


if __name__ == "__main__":
    main()