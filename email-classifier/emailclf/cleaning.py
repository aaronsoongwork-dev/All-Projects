"""Email cleaning: turn a messy real-world email into the text that actually matters.

Real emails contain HTML, quoted reply chains ("On Mon ... wrote:"), signatures and
legal disclaimers. A rejection email that quotes your earlier "Thank you for applying"
confirmation will confuse a model unless the quoted part is removed first.

All of this is heuristic (rule-of-thumb) code. It is conservative on purpose: when in
doubt it keeps text rather than deleting something important.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# --------------------------------------------------------------------------- #
# 1. HTML -> text (standard library only)
# --------------------------------------------------------------------------- #


class _TextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "head", "title"}
    BLOCK_TAGS = {"p", "div", "br", "tr", "li", "table", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


_HTML_HINT = re.compile(r"<\s*(html|body|div|p|br|table|span|a|b|i|td|tr|ul|li|h[1-6])\b", re.I)


def looks_like_html(text: str) -> bool:
    return bool(_HTML_HINT.search(text))


def strip_html(text: str) -> str:
    parser = _TextExtractor()
    parser.feed(text)
    parser.close()
    return "".join(parser.parts)


# --------------------------------------------------------------------------- #
# 2. Quoted reply chains
# --------------------------------------------------------------------------- #

_ORIGINAL_MSG = re.compile(
    r"^-{2,}\s*(original message|forwarded message)\s*-{2,}$", re.I
)
_UNDERSCORE_RULE = re.compile(r"^_{5,}$")
_HEADER_NEIGHBOURS = ("sent:", "date:", "to:", "subject:")


def _is_reply_marker(lines: list[str], i: int) -> bool:
    line = lines[i].strip()
    nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""

    # "On Mon, 3 Mar 2025 at 10:00, Name <a@b.com> wrote:"  (may wrap onto 2 lines)
    if line.startswith("On ") and ("wrote:" in line or "wrote:" in nxt):
        return True
    if _ORIGINAL_MSG.match(line) or _UNDERSCORE_RULE.match(line):
        return True
    # Outlook style header block:  From: ... / Sent: ... / To: ...
    if line.lower().startswith("from:"):
        following = [ln.strip().lower() for ln in lines[i + 1 : i + 4]]
        if any(f.startswith(_HEADER_NEIGHBOURS) for f in following):
            return True
    return False


def remove_quoted_reply(text: str) -> str:
    lines = text.split("\n")
    cut = len(lines)
    for i in range(len(lines)):
        if _is_reply_marker(lines, i):
            cut = i
            break
    kept = [ln for ln in lines[:cut] if not ln.lstrip().startswith(">")]
    result = "\n".join(kept).strip()
    # Safety net: if EVERYTHING looked quoted, keep the original instead of nothing.
    return result if result else text


# --------------------------------------------------------------------------- #
# 3. Signatures and disclaimers
# --------------------------------------------------------------------------- #

_MOBILE_SIG = re.compile(r"^\s*(sent from my .+|get outlook for .+|sent via .+)$", re.I)
_DISCLAIMER = re.compile(
    r"^\s*(confidentiality notice|disclaimer:|this (e-?mail|message)\b.{0,60}\b(confidential|intended solely))",
    re.I,
)
_CLOSING = re.compile(
    r"^\s*(best regards|kind regards|warm regards|regards|best wishes|best|sincerely|"
    r"yours sincerely|yours faithfully|cheers|thanks|thank you|many thanks)\s*[,!.]?\s*$",
    re.I,
)


def remove_signature(text: str) -> str:
    lines = text.split("\n")

    # a) the standard "-- " signature delimiter and legal disclaimers: cut everything after
    for i, line in enumerate(lines):
        if line.rstrip() == "--" or _DISCLAIMER.match(line):
            lines = lines[:i]
            break

    # b) "Sent from my iPhone" style lines
    lines = [ln for ln in lines if not _MOBILE_SIG.match(ln)]

    # c) a closing ("Best regards,") followed by a few short lines that are NOT sentences
    #    (names, job titles, phone numbers). If what follows looks like real sentences,
    #    we keep it.
    nonempty = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip()]
    for pos in range(max(0, len(nonempty) - 8), len(nonempty)):
        idx, content = nonempty[pos]
        if not _CLOSING.match(content):
            continue
        tail = [c for _, c in nonempty[pos + 1 :]]
        looks_like_sig = len(tail) <= 5 and all(
            len(c) <= 70 and not re.search(r"[.!?]$", c) for c in tail
        )
        if looks_like_sig:
            lines = lines[:idx]
            break

    return "\n".join(lines).strip()


# --------------------------------------------------------------------------- #
# 4. Small stuff
# --------------------------------------------------------------------------- #

_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_SUBJECT_PREFIX = re.compile(r"^\s*((re|fwd?|fw)\s*:\s*)+", re.I)


def normalize_subject(subject: str) -> str:
    return _SUBJECT_PREFIX.sub("", subject or "").strip()


def _normalize_whitespace(text: str) -> str:
    text = text.replace(" ", " ").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def clean_body(body: str) -> str:
    body = body or ""
    if looks_like_html(body):
        body = strip_html(body)
    body = _normalize_whitespace(body)
    body = remove_quoted_reply(body)
    body = remove_signature(body)
    body = _URL.sub("<URL>", body)
    return _normalize_whitespace(body)


def build_text(subject: str, body: str, clean: bool = True) -> str:
    """The single string that gets classified.

    clean=False is only for experiments ("how much does cleaning help?").
    """
    if clean:
        return f"Subject: {normalize_subject(subject)}\n\n{clean_body(body)}"
    return f"Subject: {subject}\n\n{body}"
