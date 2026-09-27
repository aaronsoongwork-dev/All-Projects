"""
Debug tool — check one email's SI vs BL extraction and comparison at a glance.

Usage:
    python3 check_email.py 115
    python3 check_email.py email_115          (also works)

Expects two folders sitting next to this script:
    inbox/           containing email_NNN.json files
    attachments/      containing email_NNN_SI.* and email_NNN_BL.* files

Set ANTHROPIC_API_KEY and OPENROUTER_API_KEY before running.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

try:
    from core.classifier import ClassificationResult, EmailClassifier
    from core.compare_ai import ComparisonResult, DocumentComparator
    from core.extract import FIELDS, extract_fields, extract_fields_from_image
    from core.readers.formats import render_pdf_page_as_image
    from core.readers.reader import (
        ScannedPDF,
        UnreadableAttachment,
        read_attachment_text,
    )
except ImportError:
    from classifier import ClassificationResult, EmailClassifier
    from compare_ai import ComparisonResult, DocumentComparator
    from extract import FIELDS, extract_fields, extract_fields_from_image
    from readers.formats import render_pdf_page_as_image
    from readers.reader import (
        ScannedPDF,
        UnreadableAttachment,
        read_attachment_text,
    )

INBOX_DIR = Path(__file__).parent.parent / "inbox" if (Path(__file__).parent.parent / "inbox").exists() else Path(__file__).parent / "inbox"
ATTACHMENTS_DIR = Path(__file__).parent.parent / "attachments" if (Path(__file__).parent.parent / "attachments").exists() else Path(__file__).parent / "attachments"


# ==============================================================================
# Domain Models
# ==============================================================================

@dataclass
class EmailMessage:
    """Represents an inbound email message with metadata and attachments."""
    email_id: str
    sender: str
    subject: str
    body: str
    attachments: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)

    def find_si_attachment(self) -> str | None:
        """Finds the Shipping Instruction attachment path."""
        return next((a for a in self.attachments if "_SI." in a), None)

    def find_bl_attachment(self) -> str | None:
        """Finds the draft Bill of Lading attachment path."""
        return next((a for a in self.attachments if "_BL." in a), None)

    def to_dict(self) -> dict:
        """Serializes the message into the dictionary expected by classifiers."""
        return {
            "email_id": self.email_id,
            "from": self.sender,
            "subject": self.subject,
            "body": self.body,
            "attachments": self.attachments,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmailMessage":
        return cls(
            email_id=data.get("email_id", ""),
            sender=data.get("from", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            attachments=data.get("attachments", []),
            raw_data=data,
        )

    @classmethod
    def from_file(cls, path: Path | str) -> "EmailMessage":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No such email: {path}")
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass
class VerificationReport:
    """Consolidated report produced by the email verification pipeline."""
    email: EmailMessage
    classification: ClassificationResult
    status: str  # OK, MISMATCH, NEEDS_REVIEW, NOT_COMPARISON, NO_ATTACHMENTS
    review_reason: str | None = None
    si_path: str | None = None
    bl_path: str | None = None
    si_fields: dict | None = None
    bl_fields: dict | None = None
    si_method: str | None = None
    bl_method: str | None = None
    comparison: ComparisonResult | None = None
    error_message: str | None = None


# ==============================================================================
# Services and Pipeline Components
# ==============================================================================

class AttachmentExtractor:
    """Reads document attachments and extracts shipping fields with vision fallback."""

    def __init__(self, attachments_dir: Path | str = ATTACHMENTS_DIR):
        self.attachments_dir = Path(attachments_dir)

    def extract_from_file(self, rel_path: str) -> tuple[dict, str]:
        """
        Extracts fields from an attachment file.
        Returns (fields, method) where method is 'text' or 'vision'.
        Raises UnreadableAttachment if parsing fails.
        """
        filename = rel_path.rsplit("/", 1)[-1]
        full_path = self.attachments_dir / filename
        if not full_path.exists():
            raise UnreadableAttachment(f"Attachment file not found: {full_path}")

        raw = full_path.read_bytes()
        return self.extract_from_bytes(filename, raw)

    def extract_from_bytes(self, filename: str, raw_bytes: bytes) -> tuple[dict, str]:
        """
        Extracts fields from raw bytes.
        Returns (fields, method).
        """
        try:
            text = read_attachment_text(filename, raw_bytes)
            return extract_fields(text), "text"
        except ScannedPDF as e:
            image_bytes = render_pdf_page_as_image(e.raw_bytes)
            return extract_fields_from_image(image_bytes), "vision"


def _extract_and_classify_role(filename: str, raw: bytes, extractor: "AttachmentExtractor") -> dict:
    """Runs one attachment through extraction + cheap role-sniffing. Split out
    from identify_si_bl so independent attachments can be processed on
    separate threads - extraction is an LLM call and dominates the runtime,
    so doing SI and BL in parallel roughly halves it."""
    try:
        fields, method = extractor.extract_from_bytes(filename, raw)
    except UnreadableAttachment as e:
        return {"filename": filename, "error": str(e)}

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

    return {"filename": filename, "fields": fields, "method": method, "role": role}


def identify_si_bl(
    attachments: list[tuple[str, bytes]], extractor: "AttachmentExtractor"
) -> tuple[dict, dict] | None:
    """Given a list of (filename, raw_bytes) attachments, figures out which
    one is the SI and which is the BL by reading their content (real emails
    won't reliably have '_SI'/'_BL' in the filename). Returns (si_info,
    bl_info) or None if it can't confidently tell, where each info dict has
    filename/fields/method/role (or filename/error for unreadable ones).

    Detection: look for "SHIPPING INSTRUCTION" or "BILL OF LADING" near the
    top of the extracted text. Falls back to filename hints if content is
    ambiguous. Attachments are extracted concurrently (each involves an LLM
    call) rather than one at a time.
    """
    if len(attachments) <= 1:
        docs = [_extract_and_classify_role(f, raw, extractor) for f, raw in attachments]
    else:
        with ThreadPoolExecutor(max_workers=min(len(attachments), 8)) as pool:
            docs = list(pool.map(lambda item: _extract_and_classify_role(item[0], item[1], extractor), attachments))

    identified = [d for d in docs if d.get("role") in ("SI", "BL")]
    si = next((d for d in identified if d["role"] == "SI"), None)
    bl = next((d for d in identified if d["role"] == "BL"), None)

    if si and bl:
        return si, bl
    return None  # couldn't confidently identify both roles


class EmailVerificationPipeline:
    """
    End-to-end verification pipeline:
    Classify Email -> Check Attachments -> Extract SI/BL Fields -> Compare Fields.
    """

    def __init__(
        self,
        classifier: EmailClassifier | None = None,
        extractor: AttachmentExtractor | None = None,
        comparator: DocumentComparator | None = None,
        fields: list[str] | None = None,
    ):
        self.classifier = classifier or EmailClassifier()
        self.extractor = extractor or AttachmentExtractor()
        self.comparator = comparator or DocumentComparator()
        self.fields = fields or FIELDS

    def verify(self, email: EmailMessage) -> VerificationReport:
        """Processes an email through the full verification lifecycle."""
        # 1. Classify
        classification = self.classifier.classify(email)
        if not classification.is_bl_comparison:
            return VerificationReport(
                email=email,
                classification=classification,
                status="NOT_COMPARISON",
            )

        # 2. Check attachments
        if not email.attachments:
            return VerificationReport(
                email=email,
                classification=classification,
                status="NO_ATTACHMENTS",
            )

        si_path = email.find_si_attachment()
        bl_path = email.find_bl_attachment()

        if not si_path or not bl_path:
            return VerificationReport(
                email=email,
                classification=classification,
                status="NEEDS_REVIEW",
                review_reason="missing_attachment",
                si_path=si_path,
                bl_path=bl_path,
            )

        # 3. Extract SI & BL fields
        try:
            si_fields, si_method = self.extractor.extract_from_file(si_path)
            bl_fields, bl_method = self.extractor.extract_from_file(bl_path)
        except UnreadableAttachment as e:
            return VerificationReport(
                email=email,
                classification=classification,
                status="NEEDS_REVIEW",
                review_reason="unreadable",
                si_path=si_path,
                bl_path=bl_path,
                error_message=str(e),
            )

        # 4. Compare fields
        comparison = self.comparator.compare(si_fields, bl_fields, self.fields)
        status = "MISMATCH" if comparison.has_defect else "OK"

        return VerificationReport(
            email=email,
            classification=classification,
            status=status,
            si_path=si_path,
            bl_path=bl_path,
            si_fields=si_fields,
            bl_fields=bl_fields,
            si_method=si_method,
            bl_method=bl_method,
            comparison=comparison,
        )


# ==============================================================================
# Presentation & CLI Application
# ==============================================================================

class ConsoleReporter:
    """Formats and prints verification results to the console."""

    def render_email_summary(self, email: EmailMessage):
        print(f"=== {email.email_id} ===\n")
        print(f"From:    {email.sender}")
        print(f"Subject: {email.subject}")
        body_snip = email.body[:200] + ("..." if len(email.body) > 200 else "")
        print(f"Body:    {body_snip}")
        print(f"\nAttachments ({len(email.attachments)}): {email.attachments}\n")

    def render_classification(self, classification: ClassificationResult):
        print("Classifying...")
        print(f"Category: {classification.category}\n")

    def render_report(self, report: VerificationReport, fields: list[str] | None = None):
        fields = fields or FIELDS
        self.render_email_summary(report.email)
        self.render_classification(report.classification)

        if report.status == "NOT_COMPARISON":
            print("(not a comparison request — nothing further to do)")
            return

        if report.status == "NO_ATTACHMENTS":
            print("No attachments on this email — nothing to compare.")
            return

        if report.status == "NEEDS_REVIEW" and report.review_reason == "missing_attachment":
            print(f"Missing SI or BL attachment — SI: {report.si_path}, BL: {report.bl_path}")
            print("This would be flagged NEEDS_REVIEW / missing_attachment in the real pipeline.")
            return

        if report.status == "NEEDS_REVIEW" and report.review_reason == "unreadable":
            print(f"UNREADABLE ATTACHMENT: {report.error_message}")
            print("This would be flagged NEEDS_REVIEW / unreadable in the real pipeline.")
            return

        print(f"SI: {report.si_path} (extracted via {report.si_method})")
        print(f"BL: {report.bl_path} (extracted via {report.bl_method})\n")

        if report.comparison and report.si_fields and report.bl_fields:
            print(f"{'FIELD':<20} {'SI':<35} {'BL':<35} {'MATCH'}")
            print("-" * 100)
            for field in fields:
                comp = report.comparison.field_comparisons.get(field)
                si_val = report.si_fields.get(field)
                bl_val = report.bl_fields.get(field)
                is_match = comp.is_match if comp else False
                marker = "✓" if is_match else "✗ MISMATCH"
                si_display = str(si_val)[:33] if si_val is not None else "(none)"
                bl_display = str(bl_val)[:33] if bl_val is not None else "(none)"
                print(f"{field:<20} {si_display:<35} {bl_display:<35} {marker}")
                if comp and comp.ai_reasoning:
                    print(f"  (AI check: {comp.ai_reasoning})")

            print()
            if report.status == "MISMATCH":
                print("Result: MISMATCH")
            else:
                print("Result: OK — no mismatch detected")


class EmailCheckerApp:
    """CLI controller for verifying emails."""

    def __init__(
        self,
        inbox_dir: Path | str = INBOX_DIR,
        attachments_dir: Path | str = ATTACHMENTS_DIR,
    ):
        self.inbox_dir = Path(inbox_dir)
        self.attachments_dir = Path(attachments_dir)
        self.pipeline = EmailVerificationPipeline(
            classifier=EmailClassifier(),
            extractor=AttachmentExtractor(self.attachments_dir),
            comparator=DocumentComparator(),
        )
        self.reporter = ConsoleReporter()

    @staticmethod
    def normalize_id(raw: str) -> str:
        return raw if raw.startswith("email_") else f"email_{raw.zfill(3)}"

    def check(self, raw_id: str):
        email_id = self.normalize_id(raw_id)
        email_path = self.inbox_dir / f"{email_id}.json"
        if not email_path.exists():
            print(f"Error: No such email: {email_path}")
            sys.exit(1)

        email = EmailMessage.from_file(email_path)
        try:
            report = self.pipeline.verify(email)
            self.reporter.render_report(report)
        except Exception as e:
            err_msg = str(e)
            if "Could not resolve authentication method" in err_msg or "ANTHROPIC_API_KEY" in err_msg:
                print("\n[Configuration Notice]: ANTHROPIC_API_KEY is not set.")
                print("To run extraction and comparison, set ANTHROPIC_API_KEY in your .env file or environment.")
            elif "OPENROUTER_API_KEY" in err_msg:
                print(f"\n[Configuration Notice]: {e}")
                print("To run classification, set OPENROUTER_API_KEY in your .env file or environment.")
            else:
                raise


# ==============================================================================
# Backward Compatibility Wrappers
# ==============================================================================

def normalize_id(raw: str) -> str:
    return EmailCheckerApp.normalize_id(raw)


def load_email(email_id: str) -> dict:
    path = INBOX_DIR / f"{email_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No such email: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_fields_for_attachment(rel_path: str) -> tuple[dict, str]:
    extractor = AttachmentExtractor(ATTACHMENTS_DIR)
    return extractor.extract_from_file(rel_path)


def main():
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) < 2:
        print("Usage: python3 check_email.py <email number, e.g. 115>")
        sys.exit(1)

    app = EmailCheckerApp()
    app.check(sys.argv[1])


if __name__ == "__main__":
    main()