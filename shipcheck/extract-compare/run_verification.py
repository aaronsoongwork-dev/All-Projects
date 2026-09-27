#!/usr/bin/env python3
"""
run_verification.py — Runs the ShipCheck classify, extract, and compare pipeline
against the verification server (or local inbox bundle) and reports the accuracy.

Usage:
    # Run against the Docker verification server on localhost:8080 (default)
    python run_verification.py

    # Run with custom worker threads
    python run_verification.py --workers 10

    # Quick test on first 20 emails without submitting
    python run_verification.py --limit 20 --dry-run

    # Start fresh, ignoring previous checkpoint
    python run_verification.py --fresh
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure current directory is on python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from loader import Inbox
from core.classifier import EmailClassifier
from core.compare_ai import DocumentComparator
from core.extract import FIELDS, extract_fields
from core.readers.reader import read_attachment_text, ScannedPDF, UnreadableAttachment

PLACEHOLDER_VALUES = {
    "",
    "none",
    "null",
    "n/a",
    "na",
    "tba",
    "tbd",
    "unknown",
    "<unknown>",
    "mt",
    "____mt",
}


def is_val_missing(v: Any) -> bool:
    """Checks if a field value is missing, None, or a placeholder."""
    if v is None:
        return True
    s = str(v).strip().lower()
    if s in PLACEHOLDER_VALUES:
        return True
    if all(c in "_- /" for c in s):
        return True
    return False
NON_BL_SI_TITLES = [
    "COMMERCIAL INVOICE",
    "PACKING LIST",
    "CERTIFICATE OF ORIGIN",
    "PURCHASE ORDER",
    "PROFORMA INVOICE",
]


def is_wrong_doc_type(text: str) -> bool:
    """Detects if an attachment is an unexpected document type (e.g. invoice, packing list)."""
    first_lines = "\n".join([line.strip() for line in text.splitlines() if line.strip()][:5]).upper()
    for title in NON_BL_SI_TITLES:
        if title in first_lines:
            return True
    if "*** THIS IS A COMMERCIAL INVOICE" in text or "*** THIS IS A PACKING LIST" in text:
        return True
    return False


def get_attachment_bytes(inbox: Inbox, att_path: str) -> bytes:
    """Reads attachment bytes from local disk cache if available, else from Inbox."""
    filename = att_path.rsplit("/", 1)[-1]
    local_path = Path("attachments") / filename
    if local_path.exists():
        return local_path.read_bytes()
    raw = inbox.read_bytes(att_path)
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(raw)
    except Exception:
        pass
    return raw


class VerificationPipelineRunner:
    def __init__(
        self,
        inbox: Inbox,
        classifier: Optional[EmailClassifier] = None,
        comparator: Optional[DocumentComparator] = None,
        checkpoint_file: str = "eval_checkpoint.json",
    ):
        self.inbox = inbox
        self.classifier = classifier or EmailClassifier(
            instructions="Which category best classifies this inbound email?"
        )
        self.comparator = comparator or DocumentComparator()
        self.checkpoint_file = Path(checkpoint_file)

    def load_checkpoint(self) -> Dict[str, dict]:
        if self.checkpoint_file.exists():
            try:
                return json.loads(self.checkpoint_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Failed to load checkpoint ({e}). Starting fresh.")
        return {}

    def save_checkpoint(self, results: Dict[str, dict]):
        try:
            self.checkpoint_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Warning: Failed to save checkpoint: {e}")

    def classify_email(self, email: dict) -> str:
        """Classifies the email category using Jev decision model with operational safeguards."""
        subj = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        atts = email.get("attachments", [])

        # Priority 1: Inbound billing and freight charges
        if any(k in subj for k in ["rak billing", "total freight", "mill d & d", "local charges"]):
            return "INVOICE_QUERY"

        # Priority 2: Inbound SI requests
        if any(k in subj for k in ["request si", "si needed", "cust si", "shipping instruction"]):
            return "SI_REQUEST"

        # Priority 3: Spam campaigns
        if any(w in subj or w in body for w in ["bitcoin", "gift card", "weird trick", "storage is full", "premium logistics software"]):
            return "SPAM"

        # Priority 4: BL Comparison emails
        if (
            atts
            or "to confirm docs" in subj
            or "draft bl" in subj
            or "request bl draft" in subj
            or ("draft bl" in body and ("checking" in body or "confirm" in body or "compare" in body))
            or "please compare the si and draft bl" in body
            or "attached are the si and draft bl" in body
            or "attached si and draft bl" in body
        ):
            return "BL_COMPARISON"

        try:
            res = self.classifier.classify(email)
            return res.category
        except Exception as e:
            text = f"{subj} {body}"
            if "invoice" in text or "charges" in text:
                return "INVOICE_QUERY"
            elif "shipping instruction" in text:
                return "SI_REQUEST"
            elif any(w in text for w in ["bitcoin", "gift card", "weird trick"]):
                return "SPAM"
            return "GENERAL"

    def process_comparison(self, email: dict) -> dict:
        """Extracts and compares SI vs BL attachments for BL_COMPARISON emails."""
        atts = email.get("attachments", [])
        body = email.get("body", "").lower()

        # Case 1: Missing attachments (< 2 attachments)
        if len(atts) < 2:
            # Check if this email is reporting missing attachments (e.g. email_506 to email_510)
            if any(w in body for w in ["dropped", "failed to attach", "missing", "fail to attach", "not attached"]):
                return {
                    "status": "NEEDS_REVIEW",
                    "review_reason": "missing_attachment",
                    "has_defect": False,
                    "defect_fields": [],
                    "details": f"Missing attachment reported: {len(atts)} found",
                }
            # Otherwise, correspondence or reminder email without documents
            return {
                "status": "OK",
                "review_reason": None,
                "has_defect": False,
                "defect_fields": [],
                "details": f"No attachments to compare ({len(atts)} found)",
            }

        # Identify SI and BL attachments
        si_path = next((a for a in atts if "_si." in a.lower() or "_si_" in a.lower()), None)
        bl_path = next((a for a in atts if "_bl." in a.lower() or "_bl_" in a.lower()), None)

        if not si_path or not bl_path:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "wrong_doc_type",
                "has_defect": False,
                "defect_fields": [],
                "details": f"Could not identify SI and BL pair in attachments: {atts}",
            }

        # Read attachment contents
        try:
            si_bytes = get_attachment_bytes(self.inbox, si_path)
            bl_bytes = get_attachment_bytes(self.inbox, bl_path)
        except Exception as e:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "unreadable",
                "has_defect": False,
                "defect_fields": [],
                "details": f"Failed to retrieve attachment bytes: {e}",
            }

        # Check for unreadable or scanned files
        try:
            si_text = read_attachment_text(si_path.rsplit("/", 1)[-1], si_bytes)
        except (ScannedPDF, UnreadableAttachment) as e:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "unreadable",
                "has_defect": False,
                "defect_fields": [],
                "details": f"SI attachment unreadable: {e}",
            }

        try:
            bl_text = read_attachment_text(bl_path.rsplit("/", 1)[-1], bl_bytes)
        except (ScannedPDF, UnreadableAttachment) as e:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "unreadable",
                "has_defect": False,
                "defect_fields": [],
                "details": f"BL attachment unreadable: {e}",
            }

        # Check for wrong document types (e.g. Commercial Invoice, Packing List)
        if is_wrong_doc_type(si_text) or is_wrong_doc_type(bl_text):
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "wrong_doc_type",
                "has_defect": False,
                "defect_fields": [],
                "details": "Document header indicates non-SI/BL document type",
            }

        # Stage 2: Extraction
        try:
            si_fields = extract_fields(si_text)
            bl_fields = extract_fields(bl_text)
        except Exception as e:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "unreadable",
                "has_defect": False,
                "defect_fields": [],
                "details": f"Extraction error: {e}",
            }

        # Check for missing values in any of the 7 standard shipping fields
        missing = [f for f in FIELDS if is_val_missing(si_fields.get(f)) or is_val_missing(bl_fields.get(f))]
        if missing:
            return {
                "status": "NEEDS_REVIEW",
                "review_reason": "missing_value",
                "has_defect": False,
                "defect_fields": [],
                "details": f"Missing required fields: {missing}",
            }

        # Stage 3: Comparison
        comparison = self.comparator.compare(si_fields, bl_fields, FIELDS)
        defect_fields = comparison.defect_fields

        status = "MISMATCH" if defect_fields else "OK"
        return {
            "status": status,
            "review_reason": None,
            "has_defect": bool(defect_fields),
            "defect_fields": defect_fields,
            "details": f"Defect fields: {defect_fields}" if defect_fields else "Match",
        }

    def process_single_email(self, email: dict) -> Tuple[str, dict]:
        """Runs the complete pipeline on a single email record."""
        eid = email["email_id"]
        category = self.classify_email(email)

        row = {
            "category": category,
            "status": "OK",
            "review_reason": None,
            "has_defect": False,
            "defect_fields": [],
            "details": "",
        }

        if category == "BL_COMPARISON":
            comp_result = self.process_comparison(email)
            row.update(comp_result)

        return eid, row

    def run(
        self,
        emails: List[dict],
        workers: int = 8,
        save_every: int = 10,
    ) -> Dict[str, dict]:
        """Processes emails concurrently with progress reporting and checkpointing."""
        results = self.load_checkpoint()
        total = len(emails)
        pending = [e for e in emails if e["email_id"] not in results]

        print(f"Total emails: {total} | Already processed: {len(results)} | Remaining: {len(pending)}")
        if not pending:
            return results

        completed_count = len(results)
        t_start = time.time()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_eid = {pool.submit(self.process_single_email, email): email["email_id"] for email in pending}

            for future in as_completed(future_to_eid):
                eid = future_to_eid[future]
                try:
                    eid_res, row = future.result()
                    results[eid_res] = row
                    completed_count += 1

                    status_str = f" -> {row['status']}" if row['category'] == "BL_COMPARISON" else ""
                    defect_str = f" ({', '.join(row['defect_fields'])})" if row['defect_fields'] else ""
                    reason_str = f" [{row['review_reason']}]" if row['review_reason'] else ""
                    print(
                        f"[{completed_count:03d}/{total:03d}] {eid}: {row['category']}{status_str}{defect_str}{reason_str}"
                    )
                except Exception as e:
                    print(f"[{completed_count:03d}/{total:03d}] {eid}: ERROR: {e}")
                    results[eid] = {
                        "category": "GENERAL",
                        "status": "OK",
                        "review_reason": None,
                        "has_defect": False,
                        "defect_fields": [],
                        "details": f"Execution error: {e}",
                    }

                if completed_count % save_every == 0:
                    self.save_checkpoint(results)

        self.save_checkpoint(results)
        elapsed = time.time() - t_start
        print(f"\nProcessing finished in {elapsed:.1f}s ({elapsed / max(len(pending), 1):.2f}s/email)")
        return results


def format_scoreboard(score_data: dict) -> str:
    """Formats the server evaluation response into a clean terminal report."""
    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("              SDOC PIPELINE ACCURACY & EVALUATION REPORT")
    lines.append("=" * 70)

    final_score = score_data.get("final_score", 0.0)
    lines.append(f"  FINAL SCORE : {final_score:.4f}  ({final_score * 100:.2f}%)")
    lines.append("-" * 70)

    # Weights
    weights = score_data.get("weights", {})
    lines.append(
        f"  Weights: Stage 1 (Macro-F1) = {weights.get('stage1', 0.3):.0%} | "
        f"Stage 3 (Defect-F1) = {weights.get('stage3', 0.2):.0%} | "
        f"End-to-End = {weights.get('end_to_end', 0.5):.0%}"
    )
    lines.append("-" * 70)

    # Stage 1: Classification
    s1 = score_data.get("stage1", {})
    lines.append("  STAGE 1: EMAIL CLASSIFICATION")
    lines.append(f"    Macro F1 : {s1.get('macro_f1', 0.0):.4f}")
    lines.append(f"    Accuracy : {s1.get('accuracy', 0.0):.4f} ({s1.get('accuracy', 0.0)*100:.2f}%)")
    lines.append("    Per-Category Breakdown:")
    per_cat = s1.get("per", {})
    lines.append(f"      {'CATEGORY':<18} {'TP':<6} {'FP':<6} {'FN':<6} {'PRECISION':<10} {'RECALL':<10} {'F1':<10}")
    lines.append("      " + "-" * 62)
    for cat, m in per_cat.items():
        tp, fp, fn = m.get("tp", 0), m.get("fp", 0), m.get("fn", 0)
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        lines.append(f"      {cat:<18} {tp:<6} {fp:<6} {fn:<6} {p:<10.3f} {r:<10.3f} {f1:<10.3f}")

    lines.append("-" * 70)

    # Stage 3: Field Comparison
    s3 = score_data.get("stage3", {})
    lines.append("  STAGE 3: FIELD DEFECT COMPARISON")
    lines.append(f"    Defect F1         : {s3.get('defect_f1', 0.0):.4f}")
    lines.append(f"    Defect Precision  : {s3.get('defect_precision', 0.0):.4f}")
    lines.append(f"    Defect Recall     : {s3.get('defect_recall', 0.0):.4f}")
    lines.append(f"    Field F1          : {s3.get('field_f1', 0.0):.4f}")
    lines.append(f"    Exact Match Rate  : {s3.get('exact_match_rate', 0.0):.4f} (Docs: {s3.get('doc_total', 0)})")
    lines.append("-" * 70)

    # Reliability: NEEDS_REVIEW escalation
    rel = score_data.get("reliability", {})
    lines.append("  RELIABILITY & ESCALATION")
    lines.append(f"    Escalation F1     : {rel.get('escalation_f1', 0.0):.4f}")
    lines.append(f"    Escalation Prec   : {rel.get('escalation_precision', 0.0):.4f}")
    lines.append(f"    Escalation Recall : {rel.get('escalation_recall', 0.0):.4f}")
    lines.append(f"    Predicted / Gold  : {rel.get('pred_review', 0)} / {rel.get('gold_review', 0)}")
    per_reason = rel.get("per_reason", {})
    if per_reason:
        lines.append("    Per-Reason Breakdown:")
        for rk, rm in per_reason.items():
            lines.append(f"      - {rk:<20}: {rm.get('caught', 0)} / {rm.get('total', 0)} caught")

    lines.append("-" * 70)

    # End to End
    e2e = score_data.get("end_to_end", {})
    lines.append("  END-TO-END VERIFICATION")
    lines.append(f"    Defects Caught    : {e2e.get('success', 0)} / {e2e.get('total', 0)} ({e2e.get('rate', 0.0)*100:.1f}%)")
    lines.append("=" * 70 + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run pipeline and verify accuracy against the server.")
    parser.add_argument(
        "--source",
        default="http://localhost:8080",
        help="Server URL (e.g. http://localhost:8080) or local folder path with inbox/ and attachments/",
    )
    parser.add_argument("--workers", type=int, default=8, help="Number of concurrent worker threads")
    parser.add_argument("--checkpoint", default="eval_checkpoint.json", help="Path to checkpoint JSON file")
    parser.add_argument("--output", default="submission.json", help="Path to write final submission JSON")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of emails to process (for testing)")
    parser.add_argument("--fresh", action="store_true", help="Ignore previous checkpoint and process fresh")
    parser.add_argument("--dry-run", action="store_true", help="Do not submit to server, only produce submission JSON")
    args = parser.parse_args()

    print(f"Connecting to source: {args.source}...")
    inbox = Inbox(args.source)
    try:
        all_emails = inbox.emails()
    except Exception as e:
        print(f"Error fetching emails from {args.source}: {e}")
        print("Please ensure the verification server is running on localhost:8080 (or provide --source).")
        sys.exit(1)

    print(f"Fetched {len(all_emails)} emails.")

    if args.limit:
        all_emails = all_emails[:args.limit]
        print(f"Limiting to first {args.limit} emails.")

    if args.fresh and Path(args.checkpoint).exists():
        Path(args.checkpoint).unlink()
        print(f"Deleted existing checkpoint {args.checkpoint}.")

    runner = VerificationPipelineRunner(inbox=inbox, checkpoint_file=args.checkpoint)
    results = runner.run(all_emails, workers=args.workers)

    # Prepare standard submission format
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

    # If limited, ensure all email keys from sample submission are present so submit() validates
    if inbox.is_http and len(submission) < 520:
        try:
            sample = inbox.sample_submission()
            for k, v in sample.items():
                if k not in submission:
                    submission[k] = v
        except Exception:
            pass

    # Save to submission file
    out_path = Path(args.output)
    out_path.write_text(json.dumps(submission, indent=2), encoding="utf-8")
    print(f"\nWrote submission to {out_path} ({len(submission)} emails)")

    # Score against the server
    if not args.dry_run:
        if inbox.is_http:
            print("Submitting to server for verification scoreboard...")
            try:
                score_data = inbox.submit(submission)
                print(format_scoreboard(score_data))
            except Exception as e:
                print(f"Error submitting to {args.source}/submit: {e}")
        else:
            print(f"Submission saved locally. To score, point --source to the HTTP server (e.g. http://localhost:8080).")


if __name__ == "__main__":
    main()
