#!/usr/bin/env python3
"""
loader.py — one-import access to the SDOC hackathon inbox (participants).

Works two ways with the same API:

  # A) local files (static bundle):
  from loader import Inbox
  inbox = Inbox(".")                    # folder with inbox/ + attachments/
  for email in inbox:
      print(email["email_id"], email["subject"])
      for path in email["attachments"]:
          text = inbox.read_text(path)  # SI/BL .txt content

  # B) the HTTP server (docker):
  inbox = Inbox("http://localhost:8080")
  ...                                    # identical loop
"""
import json
import os
import urllib.request
from pathlib import Path


class Inbox:
    def __init__(self, source: str = "."):
        self.source = source.rstrip("/")
        self.is_http = self.source.startswith("http://") or self.source.startswith("https://")

    # -- listing ---------------------------------------------------------
    def emails(self):
        """Return the list of email records (dicts)."""
        if self.is_http:
            return self._get_json("/emails")
        inbox_dir = Path(self.source) / "inbox"
        if not inbox_dir.exists():
            inbox_dir = Path(self.source)
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(inbox_dir.glob("email_*.json"))]

    def __iter__(self):
        return iter(self.emails())

    def get(self, email_id: str):
        if self.is_http:
            return self._get_json(f"/emails/{email_id}")
        inbox_dir = Path(self.source) / "inbox"
        if not inbox_dir.exists():
            inbox_dir = Path(self.source)
        return json.loads((inbox_dir / f"{email_id}.json").read_text(encoding="utf-8"))

    # -- attachments -----------------------------------------------------
    def read_bytes(self, att_path: str) -> bytes:
        """Raw bytes of an attachment. att_path is the string exactly as it
        appears in email['attachments'] (e.g. 'attachments/email_004_SI.txt')."""
        if self.is_http:
            return self._get_bytes("/" + att_path.lstrip("/"))
        return (Path(self.source) / att_path).read_bytes()

    def read_text(self, att_path: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(att_path).decode(encoding, errors="replace")

    # -- submission ------------------------------------------------------
    def submit(self, submission: dict) -> dict:
        """POST a submission to the server and return the scoreboard. HTTP only."""
        if not self.is_http:
            raise RuntimeError("submit() needs an HTTP source; run the docker server")
        data = json.dumps(submission).encode()
        req = urllib.request.Request(self.source + "/submit", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def sample_submission(self) -> dict:
        if self.is_http:
            return self._get_json("/sample_submission")
        path = Path(self.source) / "sample_submission.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    # -- http helpers ----------------------------------------------------
    def _get_json(self, path: str):
        with urllib.request.urlopen(self.source + path) as r:
            return json.loads(r.read())

    def _get_bytes(self, path: str) -> bytes:
        with urllib.request.urlopen(self.source + path) as r:
            return r.read()
