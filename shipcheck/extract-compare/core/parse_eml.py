"""
Parse a .eml file into the same shape check_email.py / the pipeline expect:
subject, from, body text, and a list of (filename, raw_bytes) attachments.

This is the bridge between "user exported/uploaded a real email" and the
existing readers/extract pipeline, which already knows how to handle raw
bytes for txt/pdf/docx/xlsx — nothing downstream needs to change.
"""
from email import message_from_bytes
from email.policy import default as default_policy


def parse_eml(raw: bytes) -> dict:
    msg = message_from_bytes(raw, policy=default_policy)

    body = ""
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part is not None:
        body = body_part.get_content()

    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename() or "unnamed_attachment"
        content = part.get_content()
        # get_content() returns str for text parts, bytes for binary parts
        if isinstance(content, str):
            content = content.encode("utf-8")
        attachments.append((filename, content))

    return {
        "from": msg.get("From", ""),
        "subject": msg.get("Subject", ""),
        "body": body.strip(),
        "attachments": attachments,  # [(filename, raw_bytes), ...]
    }
