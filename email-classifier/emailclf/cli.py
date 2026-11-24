"""Command line interface.  Run `python -m emailclf --help`."""

from __future__ import annotations

from regex import sub

from .data_io import Email, load_csv, load_emails, load_imap

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

from . import config
from .baseline import BaselineClassifier
from .cleaning import build_text
from .data_io import Email, load_csv, load_emails
from .evaluate import Report, evaluate, format_report, save_confusion_png, threshold_sweep
from .extraction import extract_job_info
from .feedback import append_feedback, load_training_emails
from .llm import get_client
from .pipeline import EmailPipeline
from .rules import apply_rules
from .schemas import Prediction


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _add_pipeline_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--backend", choices=["baseline", "llm"], default="baseline")
    p.add_argument("--threshold", type=float, default=None, help=f"default {config.CONFIDENCE_THRESHOLD}")
    p.add_argument("--no-clean", action="store_true", help="skip email cleaning (experiment)")
    p.add_argument("--no-rules", action="store_true", help="skip the cheap rules (experiment)")
    p.add_argument("--no-guard", action="store_true", help="skip the injection guard (experiment)")


def _build_pipeline(args, **overrides) -> EmailPipeline:
    kwargs = dict(
        backend=args.backend,
        threshold=args.threshold,
        use_rules=not args.no_rules,
        clean=not args.no_clean,
        injection_guard=not args.no_guard,
    )
    kwargs.update(overrides)
    return EmailPipeline(**kwargs)


def _run(pipeline: EmailPipeline, emails: list[Email]) -> list[Prediction]:
    preds = []
    for i, e in enumerate(emails, start=1):
        preds.append(pipeline.classify(e))
        if pipeline.backend == "llm" and i % 10 == 0:
            print(f"  ...{i}/{len(emails)}", file=sys.stderr)
    return preds


def _need_labelled(emails: list[Email]) -> list[str]:
    missing = [e.id for e in emails if e.label not in config.LABELS]
    if missing:
        sys.exit(f"These emails have no valid label (needed for evaluation): {missing[:5]}")
    return [e.label for e in emails]  # type: ignore[misc]


def _cost(preds: list[Prediction]) -> str:
    tin, tout = sum(p.tokens_in for p in preds), sum(p.tokens_out for p in preds)
    if config.PRICE_IN_PER_MTOK is None or config.PRICE_OUT_PER_MTOK is None:
        return f"{tin + tout} tokens (set PRICE_IN_PER_MTOK / PRICE_OUT_PER_MTOK in .env for $)"
    usd = tin / 1e6 * config.PRICE_IN_PER_MTOK + tout / 1e6 * config.PRICE_OUT_PER_MTOK
    return f"{tin + tout} tokens, ~${usd:.4f}"


def _mock_warning(backend: str) -> None:
    if backend == "llm" and config.LLM_PROVIDER == "mock":
        print("NOTE: LLM_PROVIDER=mock. The 'LLM' is a simple offline keyword scorer, so these numbers\n"
              "      are NOT real LLM results. Set LLM_PROVIDER in .env (see README) for the real thing.\n")


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_train(args) -> None:
    emails = load_training_emails()
    texts = [build_text(e.subject, e.body, clean=not args.no_clean) for e in emails]
    labels = [e.label for e in emails]
    counts = {c: labels.count(c) for c in config.LABELS}
    print(f"Training on {len(emails)} emails: {counts}")
    mean, std = BaselineClassifier.cross_validate(texts, labels, k=5)
    print(f"5-fold cross-validation macro-F1: {mean:.3f} (+/- {std:.3f})")
    print("  Careful: train.csv is generated from templates, so this number is optimistic.\n"
          "  The honest number is `python -m emailclf evaluate` on the hand-written test set.")
    model = BaselineClassifier.train(texts, labels)
    model.save()
    print(f"Saved model to {config.BASELINE_MODEL_PATH}")
    if args.show_words:
        for c in config.LABELS:
            words = ", ".join(w for w, _ in model.top_words(c, 8))
            print(f"  {c:<18} <- {words}")


def cmd_evaluate(args) -> None:
    _mock_warning(args.backend)
    emails = load_csv(Path(args.data))
    truth = _need_labelled(emails)
    pipeline = _build_pipeline(args)
    preds = _run(pipeline, emails)
    report = evaluate(truth, preds)
    print(format_report(report))
    print(f"\nAvg latency: {1000 * sum(p.latency_s for p in preds) / len(preds):.1f} ms/email   Cost: {_cost(preds)}")
    sources = defaultdict(int)
    for p in preds:
        sources[p.source.split(":")[0]] += 1
    print(f"Decided by: {dict(sources)}")

    if report.errors:
        print(f"\nMistakes ({len(report.errors)}):")
        for i, t, f, conf in report.errors:
            print(f"  {emails[i].id:<6} true={t:<17} predicted={f:<17} conf={conf:.2f}  | {emails[i].subject[:50]}")

    tag = args.backend + ("_noclean" if args.no_clean else "")
    config.REPORTS_DIR.mkdir(exist_ok=True)
    (config.REPORTS_DIR / f"eval_{tag}.json").write_text(
        json.dumps({"macro_f1": report.macro_f1, "accuracy": report.accuracy, "coverage": report.coverage,
                    "per_class": report.per_class, "matrix": report.matrix}, indent=2),
        encoding="utf-8",
    )
    if save_confusion_png(report, config.REPORTS_DIR / f"confusion_{tag}.png"):
        print(f"\nSaved reports/eval_{tag}.json and reports/confusion_{tag}.png")


def cmd_compare(args) -> None:
    _mock_warning("llm")
    emails = load_csv(Path(args.data))
    truth = _need_labelled(emails)
    rows = []
    for backend in ("baseline", "llm"):
        pipe = _build_pipeline(args, backend=backend)
        preds = _run(pipe, emails)
        r: Report = evaluate(truth, preds)
        rows.append((backend, r, preds))

    header = f"{'':<10}{'macro-F1':>9}{'accuracy':>10}{'coverage':>10}{'jobs->spam':>11}{'ms/email':>10}  cost"
    lines = [header]
    for backend, r, preds in rows:
        ms = 1000 * sum(p.latency_s for p in preds) / len(preds)
        lines.append(f"{backend:<10}{r.macro_f1:>9.3f}{r.accuracy:>10.1%}{r.coverage:>10.1%}{r.jobs_in_spam:>11}{ms:>10.1f}  {_cost(preds)}")
    out = "\n".join(lines)
    print(out)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    (config.REPORTS_DIR / "compare.txt").write_text(out + "\n", encoding="utf-8")
    print("\nSaved reports/compare.txt")


def cmd_sweep(args) -> None:
    _mock_warning(args.backend)
    emails = load_csv(Path(args.data))
    truth = _need_labelled(emails)
    pipeline = _build_pipeline(args, threshold=0.0)  # threshold 0 = keep every raw prediction
    preds = _run(pipeline, emails)
    print(f"{'threshold':>9}{'coverage':>10}{'accuracy on decided':>21}{'jobs->spam':>12}")
    for row in threshold_sweep(truth, preds):
        print(f"{row['threshold']:>9.2f}{row['coverage']:>10.1%}{row['accuracy_on_decided']:>21.1%}{row['jobs_in_spam']:>12}")
    print("\nRaise the threshold: fewer emails decided automatically, but those are more often right.")


def cmd_rules_report(args) -> None:
    emails = [e for p in (config.TRAIN_CSV, config.TEST_CSV) for e in load_csv(p)]
    per_rule: dict[str, list[bool]] = defaultdict(list)
    wrong = []
    for e in emails:
        hit = apply_rules(build_text(e.subject, e.body), e.sender)
        if hit:
            ok = hit.label == e.label
            per_rule[hit.rule].append(ok)
            if not ok:
                wrong.append((e.id, hit.rule, hit.label, e.label))
    covered = sum(len(v) for v in per_rule.values())
    print(f"Rules decided {covered}/{len(emails)} emails ({covered / len(emails):.1%}) without any model.\n")
    print(f"{'rule':<22}{'fired':>7}{'correct':>9}{'precision':>11}")
    for rule, oks in sorted(per_rule.items()):
        print(f"{rule:<22}{len(oks):>7}{sum(oks):>9}{sum(oks) / len(oks):>11.0%}")
    if wrong:
        print("\nWrong rule decisions (fix or delete these rules!):")
        for w in wrong:
            print("  id=%s rule=%s said=%s truth=%s" % w)
    else:
        print("\nNo wrong rule decisions on this data. (Still verify on YOUR emails.)")


def cmd_classify(args) -> None:
    _mock_warning(args.backend)
    emails = load_imap(args.limit) if args.imap else load_emails(args.input)
    if not emails:
        sys.exit(f"No emails found at {args.input}")
    pipeline = _build_pipeline(args)
    preds = _run(pipeline, emails)

    extractions: dict[int, dict] = {}
    if args.extract:
        client = get_client()
        for i, (e, p) in enumerate(zip(emails, preds)):
            if p.label.startswith("job_") or (p.label == config.REVIEW and p.raw_label.startswith("job_")):
                info, res = extract_job_info(build_text(e.subject, e.body), client)
                extractions[i] = info.model_dump() if info else {"error": res.error}

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sender", "subject", "label", "raw_label", "confidence", "source", "notes", "extracted", "body"])
        for i, (e, p) in enumerate(zip(emails, preds)):
            w.writerow([e.id, e.sender, e.subject, p.label, p.raw_label, f"{p.confidence:.2f}", p.source,
                        " | ".join(p.notes), json.dumps(extractions.get(i, {})), e.body])

    print(f"{'id':<14}{'label':<18}{'conf':>5}  subject")
    for e, p in zip(emails, preds):
        print(f"{e.id[:13]:<14}{p.label:<18}{p.confidence:>5.2f}  {e.subject[:55]}")
    print(f"\nWrote {out_path}   (contains email bodies: keep it out of git)")

    deadlines = [(extractions[i].get("deadline"), emails[i].subject, extractions[i].get("action_items"))
                 for i in extractions if extractions[i].get("deadline")]
    if deadlines:
        print("\nDeadlines found:")
        for d, subj, items in deadlines:
            print(f"  {d:<22} {subj[:45]}   {'; '.join(items or [])[:60]}")


def cmd_review(args) -> None:
    rows = list(csv.DictReader(open(args.predictions, newline="", encoding="utf-8")))
    todo = [r for r in rows if r["label"] == config.REVIEW or args.all]
    if not todo:
        print("Nothing to review.")
        return
    print(f"{len(todo)} emails to review. Type a number to set the correct label, s to skip, q to quit.\n")
    for n, c in enumerate(config.LABELS, start=1):
        print(f"  {n} = {c}")
    saved = 0
    for r in todo:
        print("\n" + "-" * 70)
        print(f"Subject: {r['subject']}\nModel guess: {r['raw_label']} (conf {r['confidence']})  notes: {r['notes']}\n")
        print(r["body"][:600])
        ans = input("\nCorrect label [1-5 / s / q]: ").strip().lower()
        if ans == "q":
            break
        if ans.isdigit() and 1 <= int(ans) <= len(config.LABELS):
            append_feedback(Email(r["id"], r["subject"], r["body"], r["sender"]), config.LABELS[int(ans) - 1])
            saved += 1
    print(f"\nSaved {saved} corrections to {config.FEEDBACK_CSV}.\nRe-train with:  python -m emailclf train")


def cmd_inject_test(args) -> None:
    _mock_warning("llm")
    emails = load_csv(config.INJECTION_CSV)
    with open(config.INJECTION_CSV, newline="", encoding="utf-8") as f:
        meta = {r["id"]: r for r in csv.DictReader(f)}

    configs = [
        ("A  naive prompt, no guard", dict(hardened_prompt=False, injection_guard=False)),
        ("B  hardened prompt, no guard", dict(hardened_prompt=True, injection_guard=False)),
        ("C  hardened prompt + guard", dict(hardened_prompt=True, injection_guard=True)),
    ]
    # Rules off and threshold 0 so we measure the MODEL/GUARD, not the safety nets.
    results: dict[str, list[Prediction]] = {}
    for name, kw in configs:
        pipe = EmailPipeline(backend="llm", threshold=0.0, use_rules=False, **kw)
        results[name] = [pipe.classify(e) for e in emails]

    print(f"{'id':<5}{'technique':<22}{'true':<15}{'attacker wants':<16}" + "".join(f"{n[0]:>15}" for n, _ in configs))
    for i, e in enumerate(emails):
        m = meta[e.id]
        print(f"{e.id:<5}{m['technique'][:21]:<22}{e.label:<15}{m['attack_target']:<16}"
              + "".join(f"{results[n][i].label:>15}" for n, _ in configs))
    print("\nA = naive prompt, no guard | B = hardened prompt | C = hardened prompt + injection guard")
    print("Fooled = the final label equals what the attacker wanted:")
    for name, _ in configs:
        fooled = sum(1 for e, p in zip(emails, results[name]) if p.label == meta[e.id]["attack_target"])
        print(f"  {name:<32} fooled {fooled}/{len(emails)}")
    print("\nLook at the email with technique 'polite-no-keywords': the regex guard cannot catch it.\n"
          "That is why you need layers (and why a human review bucket exists).")


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="emailclf", description="Job-seeker email classifier")
    parser.add_argument("-v", "--verbose", action="store_true", help="show retry/validation warnings")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("train", help="train the TF-IDF baseline")
    p.add_argument("--no-clean", action="store_true")
    p.add_argument("--show-words", action="store_true", help="print the top words per class")
    p.set_defaults(func=cmd_train)

    p.add_argument("--imap", action="store_true", help="read the newest emails from your IMAP inbox instead of --input")
    p.add_argument("--limit", type=int, default=50, help="how many inbox emails to fetch with --imap")

    for name, func, help_ in [
        ("evaluate", cmd_evaluate, "metrics + confusion matrix on the labelled test set"),
        ("sweep", cmd_sweep, "how coverage/accuracy change with the confidence threshold"),
        ("compare", cmd_compare, "baseline vs LLM: F1, latency, cost"),
    ]:
        p = sub.add_parser(name, help=help_)
        _add_pipeline_flags(p)
        p.add_argument("--data", default=str(config.TEST_CSV))
        p.set_defaults(func=func)

    p = sub.add_parser("rules-report", help="how precise are the cheap rules?")
    p.set_defaults(func=cmd_rules_report)

    p = sub.add_parser("classify", help="classify a CSV, a folder of .txt/.eml files, or one file")
    _add_pipeline_flags(p)
    p.add_argument("--input", default=str(config.DATA_DIR / "sample_inbox"))
    p.add_argument("--output", default=str(config.OUTPUT_DIR / "predictions.csv"))
    p.add_argument("--extract", action="store_true", help="also extract company/role/deadline/actions (uses the LLM provider)")
    p.add_argument("--imap", action="store_true", help="read the newest emails from your IMAP inbox instead of --input")
    p.add_argument("--limit", type=int, default=50, help="how many inbox emails to fetch with --imap")
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("review", help="fix needs_review emails; corrections become training data")
    p.add_argument("--predictions", default=str(config.OUTPUT_DIR / "predictions.csv"))
    p.add_argument("--all", action="store_true", help="review every email, not just needs_review")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("inject-test", help="try prompt-injection emails against 3 defence levels")
    p.set_defaults(func=cmd_inject_test)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.ERROR, format="%(levelname)s %(message)s")
    args.func(args)
