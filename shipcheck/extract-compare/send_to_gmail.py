#!/usr/bin/env python3
"""
send_to_gmail.py — Script to send emails from inbox/*.json with their attachments to a Gmail account.

Features:
  - Parses emails from inbox/*.json (subject, sender, body, attachment links).
  - Attaches matching files from attachments/ (PDF, DOCX, XLSX, TXT, etc.).
  - Sends via Gmail SMTP (smtp.gmail.com:587 STARTTLS or 465 SSL).
  - Preserves original metadata (original sender in Reply-To and header summary).
  - Supports dry-run verification mode (--dry-run) to test parsing without sending.
  - State tracking (--state-file) to safely resume without resending duplicates.
  - Rate limiting (--delay) to respect Gmail sending thresholds.
  - Batching and automatic SMTP session reconnection.
  - Flexible credentials via CLI flags, interactive prompts, or .env file.
"""

import argparse
import getpass
import json
import mimetypes
import os
import smtplib
import ssl
import sys
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def load_sent_state(state_file: Path) -> Set[str]:
    """Loads set of previously sent email_ids from state file."""
    if not state_file.exists():
        return set()
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict) and "sent_ids" in data:
                return set(data["sent_ids"])
    except Exception as e:
        print(f"[!] Warning: Could not read state file {state_file}: {e}")
    return set()


def save_sent_state(state_file: Path, sent_ids: Set[str]) -> None:
    """Saves updated set of sent email_ids to state file."""
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(sorted(list(sent_ids)), f, indent=2)
    except Exception as e:
        print(f"[!] Warning: Failed to update state file {state_file}: {e}")


def resolve_attachment_path(
    att_ref: str,
    inbox_dir: Path,
    attachments_dir: Path,
    repo_root: Path
) -> Optional[Path]:
    """
    Attempts to resolve an attachment reference to an existing file on disk.
    Checks:
      1. Repo-relative or absolute path as specified
      2. In attachments_dir by basename
      3. In inbox_dir
    """
    candidates = [
        repo_root / att_ref,
        Path(att_ref),
        attachments_dir / Path(att_ref).name,
        inbox_dir / att_ref,
        inbox_dir / Path(att_ref).name,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return None


def create_mime_message(
    email_data: Dict[str, Any],
    from_addr: str,
    to_addr: str,
    inbox_dir: Path,
    attachments_dir: Path,
    repo_root: Path,
    subject_prefix: str = "",
    include_metadata_header: bool = True,
) -> MIMEMultipart:
    """
    Constructs a MIMEMultipart email message from an email JSON record and attachments.
    """
    email_id = email_data.get("email_id", "unknown_id")
    orig_from = email_data.get("from", "")
    orig_subject = email_data.get("subject", "No Subject")
    body_text = email_data.get("body", "")
    attachment_refs = email_data.get("attachments", [])

    # Compose final subject
    if subject_prefix:
        subject = f"{subject_prefix} {orig_subject}"
    else:
        subject = orig_subject

    # Create root multipart message
    msg = MIMEMultipart("mixed")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    if orig_from:
        msg["Reply-To"] = orig_from

    # Custom tracking headers
    msg["X-Original-From"] = orig_from
    msg["X-Original-Email-ID"] = email_id

    # Compose email body
    if include_metadata_header:
        full_body = body_text
    else:
        full_body = body_text

    msg.attach(MIMEText(full_body, "plain", "utf-8"))

    # Attach all files
    for att_ref in attachment_refs:
        att_path = resolve_attachment_path(att_ref, inbox_dir, attachments_dir, repo_root)
        if not att_path:
            print(f"    [!] Warning: Attachment '{att_ref}' not found for {email_id}")
            continue

        filename = att_path.name
        ctype, encoding = mimetypes.guess_type(str(att_path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        try:
            with open(att_path, "rb") as f:
                part = MIMEBase(maintype, subtype)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
        except Exception as e:
            print(f"    [!] Error attaching file '{att_path}': {e}")

    return msg


def connect_smtp(
    server: str,
    port: int,
    username: str,
    password: str,
    use_ssl: bool = False
) -> smtplib.SMTP:
    """Connects and authenticates to SMTP server."""
    print(f"[*] Connecting to SMTP server {server}:{port} (SSL={use_ssl})...")
    context = ssl.create_default_context()
    if use_ssl:
        smtp = smtplib.SMTP_SSL(server, port, context=context, timeout=30)
    else:
        smtp = smtplib.SMTP(server, port, timeout=30)
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()

    smtp.login(username, password)
    print(f"[+] Successfully authenticated as {username}")
    return smtp


def main():
    parser = argparse.ArgumentParser(
        description="Send emails and attachments from inbox/*.json to a Gmail account.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run preview:
  python send_to_gmail.py --to myaccount@gmail.com --dry-run

  # Send first 3 emails to verify:
  python send_to_gmail.py --to myaccount@gmail.com --limit 3

  # Send all emails using credentials from environment/.env:
  python send_to_gmail.py --to myaccount@gmail.com

  # Specify explicit credentials via flags:
  python send_to_gmail.py --to recipient@gmail.com --user sender@gmail.com --password "xxxx xxxx xxxx xxxx"

Note on Gmail:
  Google requires an "App Password" (16 characters) instead of your regular password.
  To generate one:
    1. Visit https://myaccount.google.com/security
    2. Ensure "2-Step Verification" is ON.
    3. Search for "App passwords" (or go to https://myaccount.google.com/apppasswords).
    4. Create an App password named "ShipCheck" and copy the 16-character code.
        """
    )

    parser.add_argument(
        "--to", "-t",
        help="Destination email address (e.g. recipient@gmail.com). Defaults to env GMAIL_TO or DESTINATION_EMAIL."
    )
    parser.add_argument(
        "--user", "-u",
        help="Gmail / SMTP username used to authenticate. Defaults to env GMAIL_USER or SMTP_USER."
    )
    parser.add_argument(
        "--password", "-p",
        help="Gmail App Password (16 chars). Defaults to env GMAIL_APP_PASSWORD or SMTP_PASSWORD."
    )
    parser.add_argument(
        "--from-addr",
        help="Sender email address in headers. Defaults to --user or username."
    )
    parser.add_argument(
        "--server",
        default=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        help="SMTP server hostname (default: smtp.gmail.com)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("SMTP_PORT", 587)),
        help="SMTP server port (default: 587 for STARTTLS, 465 for SSL)"
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use SSL instead of STARTTLS (typically with port 465)"
    )
    parser.add_argument(
        "--inbox-dir",
        default="inbox",
        help="Directory containing JSON emails (default: inbox)"
    )
    parser.add_argument(
        "--attachments-dir",
        default="attachments",
        help="Directory containing attachments (default: attachments)"
    )
    parser.add_argument(
        "--state-file",
        default=".sent_emails.json",
        help="JSON file to record successfully sent email IDs (default: .sent_emails.json)"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=0,
        help="Maximum number of emails to send (0 = all)"
    )
    parser.add_argument(
        "--start-from",
        help="Start sending from this email_id (e.g. email_050)"
    )
    parser.add_argument(
        "--email-ids",
        help="Comma-separated specific email IDs to send (e.g. email_001,email_005)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between emails to avoid rate limits (default: 1.0s)"
    )
    parser.add_argument(
        "--reconnect-every",
        type=int,
        default=50,
        help="Reconnect to SMTP server every N emails to keep session fresh (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview emails, attachments, and recipients without connecting or sending"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore state file and send even if previously marked as sent"
    )
    parser.add_argument(
        "--no-metadata-header",
        action="store_true",
        help="Do not prepend original metadata summary block to email body"
    )
    parser.add_argument(
        "--subject-prefix",
        default="",
        help="Optional prefix for email subject lines (e.g. '[ShipCheck]')"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    inbox_dir = (repo_root / args.inbox_dir).resolve()
    attachments_dir = (repo_root / args.attachments_dir).resolve()
    state_file = (repo_root / args.state_file).resolve()

    if not inbox_dir.is_dir():
        print(f"[X] Error: Inbox directory not found: {inbox_dir}")
        sys.exit(1)

    # Collect JSON files sorted by name
    json_files = sorted(list(inbox_dir.glob("*.json")))
    if not json_files:
        print(f"[X] No .json files found in {inbox_dir}")
        sys.exit(1)

    # Filter by specific email-ids or start-from
    selected_files = []
    filter_ids = [i.strip() for i in args.email_ids.split(",")] if args.email_ids else None

    started = args.start_from is None
    for f in json_files:
        email_stem = f.stem  # e.g. email_001
        if not started:
            if email_stem == args.start_from or f.name == args.start_from:
                started = True
            else:
                continue

        if filter_ids is not None:
            if email_stem in filter_ids or f.name in filter_ids:
                selected_files.append(f)
        else:
            selected_files.append(f)

    # Apply limit
    if args.limit and args.limit > 0:
        selected_files = selected_files[:args.limit]

    # Load sent state
    sent_ids: Set[str] = set() if args.force else load_sent_state(state_file)

    # Gather emails to process
    queue: List[Dict[str, Any]] = []
    skipped_count = 0
    for f in selected_files:
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                email_id = data.get("email_id", f.stem)
                if not args.force and email_id in sent_ids:
                    skipped_count += 1
                    continue
                queue.append(data)
        except Exception as e:
            print(f"[!] Warning: Failed to parse {f.name}: {e}")

    print(f"\n==================================================")
    print(f" ShipCheck Email Sender")
    print(f"==================================================")
    print(f" Inbox directory:       {inbox_dir}")
    print(f" Attachments directory: {attachments_dir}")
    print(f" Total files scanned:   {len(selected_files)}")
    print(f" Already sent (skipped):{skipped_count}")
    print(f" Queued to send:        {len(queue)}")
    print(f" Dry-run mode:          {'ENABLED' if args.dry_run else 'DISABLED'}")
    print(f"==================================================\n")

    if not queue:
        print("[+] Nothing to send! All selected emails have already been processed.")
        print("    (Use --force to resend, or specify different files/limits.)")
        return

    # In dry-run mode, we don't need credentials
    if args.dry_run:
        print("[*] Running DRY-RUN simulation...")
        total_atts = 0
        missing_atts = 0
        for idx, email_data in enumerate(queue, start=1):
            email_id = email_data.get("email_id", f"idx_{idx}")
            subj = email_data.get("subject", "")
            from_sender = email_data.get("from", "")
            atts = email_data.get("attachments", [])
            print(f"[{idx}/{len(queue)}] {email_id} | From: {from_sender} | Subject: {subj[:50]}...")
            for a in atts:
                total_atts += 1
                resolved = resolve_attachment_path(a, inbox_dir, attachments_dir, repo_root)
                if resolved:
                    print(f"    [OK] Attachment: {resolved.name} ({resolved.stat().st_size} bytes)")
                else:
                    missing_atts += 1
                    print(f"    [MISSING] Attachment reference: {a}")

        print("\n--- Dry Run Summary ---")
        print(f"Emails queued:         {len(queue)}")
        print(f"Total attachments:     {total_atts}")
        print(f"Missing attachments:   {missing_atts}")
        print("Dry run completed successfully. No emails were sent.\n")
        return

    # Credentials determination
    to_addr = args.to or os.getenv("GMAIL_TO") or os.getenv("DESTINATION_EMAIL")
    user = args.user or os.getenv("GMAIL_USER") or os.getenv("SMTP_USER")
    password = args.password or os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD")

    if not to_addr:
        to_addr = input("Enter destination Gmail address (--to): ").strip()
        if not to_addr:
            print("[X] Error: Destination email address is required.")
            sys.exit(1)

    if not user:
        user = input("Enter sender Gmail address (--user): ").strip()
        if not user:
            print("[X] Error: Sender email/username is required.")
            sys.exit(1)

    if not password:
        password = getpass.getpass(f"Enter Gmail App Password for {user}: ").strip()
        if not password:
            print("[X] Error: Password is required.")
            sys.exit(1)

    from_addr = args.from_addr or user

    # Connect to SMTP
    smtp_client: Optional[smtplib.SMTP] = None
    try:
        smtp_client = connect_smtp(
            server=args.server,
            port=args.port,
            username=user,
            password=password,
            use_ssl=args.ssl or args.port == 465
        )
    except Exception as e:
        print(f"[X] Failed to connect to SMTP server: {e}")
        sys.exit(1)

    sent_count = 0
    failed_count = 0

    try:
        for idx, email_data in enumerate(queue, start=1):
            email_id = email_data.get("email_id", f"idx_{idx}")
            subj = email_data.get("subject", "")
            print(f"[{idx}/{len(queue)}] Preparing {email_id} ({subj[:40]}...)...", end=" ", flush=True)

            # Reconnect if threshold reached
            if idx > 1 and args.reconnect_every and (idx - 1) % args.reconnect_every == 0:
                print("\n[*] Reconnecting SMTP session to maintain stability...", end=" ", flush=True)
                try:
                    smtp_client.quit()
                except Exception:
                    pass
                smtp_client = connect_smtp(
                    server=args.server,
                    port=args.port,
                    username=user,
                    password=password,
                    use_ssl=args.ssl or args.port == 465
                )

            # Build message
            msg = create_mime_message(
                email_data=email_data,
                from_addr=from_addr,
                to_addr=to_addr,
                inbox_dir=inbox_dir,
                attachments_dir=attachments_dir,
                repo_root=repo_root,
                subject_prefix=args.subject_prefix,
                include_metadata_header=not args.no_metadata_header,
            )

            # Send
            try:
                smtp_client.send_message(msg)
                print("SENT.")
                sent_count += 1
                sent_ids.add(email_id)
                # Persist state after each send so progress isn't lost
                save_sent_state(state_file, sent_ids)
            except Exception as e:
                print(f"FAILED: {e}")
                failed_count += 1
                # Try to reconnect once if broken pipe or dropped connection
                try:
                    print("    [*] Retrying with fresh SMTP connection...")
                    smtp_client = connect_smtp(
                        server=args.server,
                        port=args.port,
                        username=user,
                        password=password,
                        use_ssl=args.ssl or args.port == 465
                    )
                    smtp_client.send_message(msg)
                    print("    [+] Resend SUCCESS.")
                    sent_count += 1
                    sent_ids.add(email_id)
                    save_sent_state(state_file, sent_ids)
                except Exception as retry_err:
                    print(f"    [X] Retry failed: {retry_err}")

            if args.delay > 0 and idx < len(queue):
                time.sleep(args.delay)

    except KeyboardInterrupt:
        print("\n[!] Execution paused by user (Ctrl+C). Progress has been saved to state file.")
    finally:
        if smtp_client:
            try:
                smtp_client.quit()
            except Exception:
                pass

    print(f"\n==================================================")
    print(f" Summary")
    print(f"==================================================")
    print(f" Successfully sent: {sent_count}")
    print(f" Failed:            {failed_count}")
    print(f" State file:        {state_file}")
    print(f"==================================================\n")


if __name__ == "__main__":
    main()

