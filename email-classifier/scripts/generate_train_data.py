"""Generate a SYNTHETIC training set (data/train.csv) from templates.

Run:  python scripts/generate_train_data.py            (48 emails per class, seed 42)
      python scripts/generate_train_data.py --per-class 100 --seed 7

Why synthetic? You have no labelled data yet and must not put real emails on GitHub.
Why messy? Each email is randomly decorated with a greeting, signature, HTML wrapper,
legal disclaimer, marketing footer, or a quoted earlier message (taken from a random
OTHER class), so that the cleaning step genuinely matters.

IMPORTANT LIMITATION: templates are repetitive, so a model scores unrealistically well
when tested on the same templates (cross-validation). The hand-written data/test.csv is
the honest benchmark. Replace this data with your own labelled (anonymised) emails when
you can. Feedback from `python -m emailclf review` is appended on top of it.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMPANIES = ["Brightwave Systems", "Nordlane Analytics", "Kopi Labs", "Orchid Labs", "Zenith Pay",
             "Halcyon Cloud", "Pinecrest Digital", "Tidewater Data", "Mosaic Robotics", "Lumen Health"]
ROLES = ["AI Engineer", "Data Scientist", "Backend Engineer", "Machine Learning Engineer", "Data Analyst",
         "Python Developer", "Data Engineer", "DevOps Engineer", "Software Engineer", "NLP Engineer"]
NAMES = ["Aisyah", "Wei Jie", "Priya", "Daniel", "Siti", "Arjun", "Mei Ling", "Hafiz", "Nur", "Kevin"]
RECRUITERS = ["Farah", "Marcus", "Jun Wei", "Sam", "Priya", "Iqbal", "Mei Ling", "Oliver", "Daniel", "Nadia"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MONTHS = ["January", "February", "March", "April", "May", "June"]
URLS = ["http://claim-now.example/x1", "https://portal.example/c/883", "http://secure-check.example/v", "https://assess.example/t/77"]

TEMPLATES: dict[str, list[str]] = {
    "spam": [
        "Dear {name}, you have won a ${amt} gift card! Claim your prize here: {url}. Offer expires in 24 hours. Click now!",
        "Earn ${amt} per day working from home. No experience needed, no interview. Message us on WhatsApp to start. Limited spots!",
        "Your account has been suspended. Verify your account immediately at {url} to avoid closure.",
        "Special discount: {pct}% off everything this weekend only! Shop now at {url}. Unsubscribe at any time.",
        "Make your money grow with our crypto fund. Guaranteed {pct}% returns, zero risk. Join today: {url}",
        "Congratulations, you are hired as a {role} at {company}! To receive your contract send a processing fee of RM {fee} to the account below.",
        "We can get your website to page 1 of Google fast. Free SEO report for {name}. Reply YES.",
        "Buy {n} followers for only ${amt}. Limited time bonus. Order now at {url}.",
    ],
    "job_offer": [
        "Dear {name}, we are pleased to offer you the position of {role} at {company}. Salary: RM {salary} per month. Start date: {day} {month}. Please find the offer letter attached.",
        "Hi {name}, I'm a recruiter at {company}. We're hiring a {role} (hybrid, Kuala Lumpur). Your profile looks like a great match. Open to a quick call this week?",
        "Congratulations {name}! After your interviews we would like to extend an offer for the {role} role at {company}, compensation RM {salary} per month.",
        "Role: {role}. Location: KL. Salary: RM {salary_low}-{salary_high}. Interested? Reply and I'll send the full job description.",
        "We're looking for a {role} to join {company} on a {months}-month contract. Rate RM {rate} per day. Would you be interested in hearing more?",
        "As discussed on our call, I'm happy to confirm our offer of the {role} position at {company}, starting {day} {month}. Welcome to the team!",
        "I saw your portfolio and think you'd be perfect for an opening on our team at {company}: {role}, fully remote. Let me know if you'd like to be referred.",
    ],
    "job_task": [
        "Hi {name}, as the next step please complete the online assessment using this link: {url}. You have {days} days to complete it.",
        "Please submit your transcript, a copy of your ID and two references by {weekday} through the candidate portal.",
        "Please select an interview slot using the scheduling link: {url}. Slots are open until {weekday} {day} {month}.",
        "Please complete the attached take-home task and send us your GitHub link within {hours} hours.",
        "Before we can continue, please fill in the background check form: {url}. It must be completed within {days} business days.",
        "Could you please confirm your availability for an interview on {weekday} or {weekday2}? Reply to this email.",
        "Please sign and return your contract and complete the onboarding forms before your first day on {day} {month}.",
    ],
    "job_confirmation": [
        "Thank you for applying for the {role} position at {company}. We have received your application and will review it shortly.",
        "This is to confirm your interview on {weekday} {day} {month} at {time} via Zoom.",
        "We have received your assessment submission. Our team will review it and update you in {days} days.",
        "Thank you for accepting our offer! We are delighted to welcome you as {role} on {day} {month}. Your signed contract has been received.",
        "Your documents have been received and your file is complete. No further action is needed from you.",
        "Your interview has been rescheduled to {weekday} at {time}. A new calendar invite has been sent.",
        "Your application for {role} is currently under review. There is nothing you need to do right now.",
    ],
    "job_rejection": [
        "Thank you for your interest in {company}. Unfortunately we have decided to move forward with other candidates for the {role} role.",
        "After careful consideration, we will not be moving forward with your application for {role}. We wish you the best in your search.",
        "We regret to inform you that you have not been selected for the {role} position.",
        "The {role} position has been filled. We appreciate your time and encourage you to apply again.",
        "Your profile isn't the right fit for this role at this time. We will keep your CV on file for future openings.",
        "We received many strong applications and unfortunately we are unable to offer you an interview for {role}.",
        "Thank you for interviewing with us. This was a close call but we have decided not to offer you the role.",
    ],
}

SUBJECTS: dict[str, list[str]] = {
    "spam": ["You've been selected!", "Final notice", "Limited time offer", "Re: your request", "Exclusive deal for {name}", "Urgent!!", "Make money fast"],
    "job_offer": ["Opportunity at {company}", "Offer of employment - {role}", "{role} role - are you interested?", "Job opportunity", "Your offer from {company}"],
    "job_task": ["Action required: {company}", "Next steps - {role}", "Please complete your application", "Reminder: deadline approaching", "Your assessment link"],
    "job_confirmation": ["Application received - {role}", "Interview confirmed", "Confirmation: {company}", "We got your submission", "Application status"],
    "job_rejection": ["Update on your application", "Your application to {company}", "Application outcome", "Thank you for interviewing", "Regarding the {role} position"],
}

DISCLAIMER = ("CONFIDENTIALITY NOTICE: This email and any attachments are intended solely for the addressee "
              "and may contain confidential information. If you received it in error, please delete it.")
FOOTERS = ["You are receiving this email because you registered on our careers portal. Unsubscribe | Manage preferences",
           "This is an automated message. Please do not reply. Unsubscribe from job alerts."]


def slots(rng: random.Random) -> dict:
    low = rng.randrange(4000, 9000, 500)
    return dict(
        name=rng.choice(NAMES), company=rng.choice(COMPANIES), role=rng.choice(ROLES), url=rng.choice(URLS),
        amt=rng.choice([200, 500, 750, 1000, 5000]), pct=rng.choice([50, 70, 90, 200, 300]),
        fee=rng.choice([150, 200, 300]), n=rng.choice([1000, 5000, 10000]), salary=rng.randrange(4500, 12000, 100),
        salary_low=low, salary_high=low + 2000, months=rng.choice([3, 6, 12]), rate=rng.randrange(400, 900, 50),
        day=rng.randint(1, 28), month=rng.choice(MONTHS), days=rng.choice([3, 5, 7]), hours=rng.choice([48, 72]),
        weekday=rng.choice(WEEKDAYS), weekday2=rng.choice(WEEKDAYS), time=rng.choice(["10:00", "14:00", "15:30"]),
    )


def decorate(label: str, body: str, s: dict, rng: random.Random, other_bodies: list[str]) -> str:
    """Make the email look like real mail: greeting, signature, quotes, HTML, footers."""
    sender_name = rng.choice(RECRUITERS)
    if label != "spam" and rng.random() < 0.5 and not body.startswith(("Hi", "Dear", "Congrat")):
        body = f"Hi {s['name']},\n\n{body}"
    if label != "spam" and rng.random() < 0.55:
        body += f"\n\n{rng.choice(['Best regards', 'Kind regards', 'Thanks', 'Regards', 'Cheers'])},\n{sender_name}\nTalent Team\n{s['company']}"
        if rng.random() < 0.5:
            body += f"\n+60 3-{rng.randint(1000, 9999)} {rng.randint(1000, 9999)}"
    if rng.random() < 0.12:
        body += "\n\nSent from my iPhone"
    if rng.random() < 0.15:
        body += f"\n\n{DISCLAIMER}"
    if label != "spam" and rng.random() < 0.15:
        body += f"\n\n{rng.choice(FOOTERS)}"
    if rng.random() < 0.25:  # quoted earlier message from a random OTHER email (noise)
        quoted = rng.choice(other_bodies).replace("\n", "\n> ")
        body += (f"\n\nOn {rng.choice(WEEKDAYS)}, {rng.randint(1, 28)} {rng.choice(MONTHS)} 2025 at 09:{rng.randint(10, 59)}, "
                 f"{rng.choice(NAMES)} <{rng.choice(NAMES).lower()}@example.com> wrote:\n> {quoted}")
    if rng.random() < 0.25:  # wrap as HTML
        paragraphs = "".join(f"<p>{p}</p>" for p in body.split("\n\n")).replace("\n", "<br>")
        body = f'<html><body><div style="font-family:Arial">{paragraphs}</div></body></html>'
    return body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=48)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ROOT / "data" / "train.csv"))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    all_templates = [t for ts in TEMPLATES.values() for t in ts]
    rows = []
    for label, templates in TEMPLATES.items():
        for i in range(args.per_class):
            s = slots(rng)
            body = rng.choice(templates).format(**s)
            other = [rng.choice(all_templates).format(**slots(rng)) for _ in range(3)]
            body = decorate(label, body, s, rng, other)
            subject = rng.choice(SUBJECTS[label]).format(**s)
            if rng.random() < 0.15:
                subject = "Re: " + subject
            domain = "free-prizes.example" if label == "spam" and rng.random() < 0.1 else (
                f"{rng.choice(['promo', 'deals', 'info'])}@{rng.choice(['bigdeals', 'quickmoney', 'bestoffer'])}.example"
                if label == "spam" else f"hr@{s['company'].split()[0].lower()}.example")
            sender = domain if "@" in domain else f"promo@{domain}"
            rows.append({"id": f"{label[:3]}{i:03d}", "sender": sender, "subject": subject, "body": body, "label": label})
    rng.shuffle(rows)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "sender", "subject", "body", "label"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} synthetic emails to {args.out}")


if __name__ == "__main__":
    main()
