"""Loading emails from CSV, a folder of .txt files, or a folder of .eml files.

CSV columns:   id (optional), sender (optional), subject, body, label (optional)
.txt format:   optional "Subject: ..." and "From: ..." lines at the top, blank line, body.
IMAP:          load_imap() reads the newest emails from your inbox (read-only).
"""

from __future__ import annotations

import csv
import imaplib
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path

from . import config

csv.field_size_limit(10_000_000)


@dataclass
class Email:
    id: str
    subject: str
    body: str
    sender: str = ""
    label: str | None = None


def load_csv(path: Path) -> list[Email]:
    emails: list[Email] = []
    with open(path, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=1):
            emails.append(
                Email(
                    id=(row.get("id") or f"row{n}").strip(),
                    subject=row.get("subject", "") or "",
                    body=row.get("body", "") or "",
                    sender=row.get("sender", "") or "",
                    label=(row.get("label") or "").strip() or None,
                )
            )
    return emails

# reads the email header (sender, receiver, subject, date)
def parse_txt(path: Path) -> Email:
    text = path.read_text(encoding="utf-8", errors="replace")
    subject, sender = "", ""
    lines = text.split("\n")
    body_start = 0
    for i, line in enumerate(lines[:10]):
        low = line.lower()
        if low.startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
        elif low.startswith("from:"):
            sender = line.split(":", 1)[1].strip()
            body_start = i + 1
        elif not line.strip():
            body_start = i + 1
            break
        else:
            break
    return Email(id=path.stem, subject=subject, body="\n".join(lines[body_start:]).strip(), sender=sender)

def parse_message(msg, id_: str) -> Email:
    part = msg.get_body(preferencelist=("plain", "html"))
    body = part.get_content() if part is not None else ""
    return Email(id=id_, subject=str(msg["subject"] or ""), body=body, sender=str(msg["from"] or ""))


def parse_eml(path: Path) -> Email:
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return parse_message(msg, path.stem)

def load_folder(path: Path) -> list[Email]:
    emails: list[Email] = []
    for file in sorted(path.iterdir()):
        if file.suffix.lower() == ".txt":
            emails.append(parse_txt(file))
        elif file.suffix.lower() == ".eml":
            emails.append(parse_eml(file))
    return emails


def load_emails(path: str | Path) -> list[Email]:
    path = Path(path)
    if path.is_dir():
        return load_folder(path)
    if path.suffix.lower() == ".csv":
        return load_csv(path)
    if path.suffix.lower() == ".eml":
        return [parse_eml(path)]
    return [parse_txt(path)]

def load_imap(limit: int = 50) -> list[Email]:
    if not (config.IMAP_HOST and config.IMAP_USER and config.IMAP_PASSWORD):
        raise SystemExit("Set IMAP_HOST, IMAP_USER and IMAP_PASSWORD in .env first.")
    out: list[Email] = []
    with imaplib.IMAP4_SSL(config.IMAP_HOST) as imap:
        imap.login(config.IMAP_USER, config.IMAP_PASSWORD)
        imap.select("INBOX", readonly=True)  # read-only: cannot change your mailbox
        _, data = imap.uid("search", None, "ALL")
        uids = data[0].split()[-limit:][::-1]  # newest first
        for uid in uids:
            _, msg = imap.uid("fetch", uid, "(BODY.PEEK[])")  # PEEK = don't mark as read
            if not msg or not msg[0] or not isinstance(msg[0], tuple):
                continue
            parsed = BytesParser(policy=policy.default).parsebytes(msg[0][1])
            out.append(parse_message(parsed, uid.decode()))
    return out