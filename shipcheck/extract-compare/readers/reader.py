"""
Format dispatcher. Single entry point the rest of the pipeline calls — hides
which library handles which extension, and turns read failures into clean,
distinguishable signals:

  - UnreadableAttachment: genuinely broken (corrupt file, unsupported
    format). Nothing more to try — escalate as NEEDS_REVIEW / unreadable.
  - ScannedPDF: the PDF opened fine but has no text layer — almost always
    means it's a scanned image. Carries the raw bytes so the caller can
    attempt the vision fallback (render page -> image -> Claude vision)
    before giving up.
"""
try:
    from core.readers.formats import READERS_BY_EXT, read_pdf
except ImportError:
    try:
        from readers.formats import READERS_BY_EXT, read_pdf
    except ImportError:
        from formats import READERS_BY_EXT, read_pdf


class UnreadableAttachment(Exception):
    """Genuinely broken — corrupt file or unsupported format. No fallback
    left to try; the pipeline should escalate to NEEDS_REVIEW / unreadable."""


class ScannedPDF(Exception):
    """A PDF that opened without error but extracted to empty text — almost
    certainly a scanned image with no text layer. Carries the raw bytes so
    the caller can try rendering it to an image and using vision extraction
    before falling back to UnreadableAttachment."""

    def __init__(self, message: str, raw_bytes: bytes):
        super().__init__(message)
        self.raw_bytes = raw_bytes


def read_attachment_text(att_path: str, raw: bytes) -> str:
    ext = att_path.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        try:
            text = read_pdf(raw)
        except Exception as e:  # noqa: BLE001
            raise UnreadableAttachment(f"Failed to read {att_path}: {e}") from e
        if not text.strip():
            raise ScannedPDF(f"{att_path} has no text layer (likely scanned)", raw)
        return text

    reader = READERS_BY_EXT.get(ext)
    if reader is None:
        raise UnreadableAttachment(f"No reader for extension '.{ext}' ({att_path})")
    try:
        text = reader(raw)
    except Exception as e:  # noqa: BLE001
        raise UnreadableAttachment(f"Failed to read {att_path}: {e}") from e
    if not text.strip():
        raise UnreadableAttachment(f"{att_path} extracted to empty text")
    return text
