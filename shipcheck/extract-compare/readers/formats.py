"""
Format-specific readers. Each function takes raw bytes and returns a single
plain-text string suitable for feeding to the extraction LLM prompt.
No field parsing here — just "get all the readable text out of this file".
"""
import io


def read_txt(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def read_pdf(raw: bytes) -> str:
    import pdfplumber

    parts = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
            for table in page.extract_tables():
                for row in table:
                    parts.append(" | ".join(c or "" for c in row))
    return "\n".join(parts)


def read_docx(raw: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(raw))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(parts)


def read_xlsx(raw: bytes) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    parts = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def render_pdf_page_as_image(raw: bytes, page_num: int = 0, dpi: int = 200) -> bytes:
    """Render one page of a PDF to PNG bytes. Used as a fallback when a PDF
    has no extractable text layer (i.e. it's a scanned image)."""
    import pymupdf

    doc = pymupdf.open(stream=raw, filetype="pdf")
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")


READERS_BY_EXT = {
    "txt": read_txt,
    "pdf": read_pdf,
    "docx": read_docx,
    "xlsx": read_xlsx,
}
