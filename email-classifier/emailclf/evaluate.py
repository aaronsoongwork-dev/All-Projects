"""Metrics, written by hand so you can SEE the Day 1 formulas:

    precision = TP / (TP + FP)    "when I say 'spam', how often am I right?"
    recall    = TP / (TP + FN)    "of all the real spam, how much did I catch?"
    F1        = 2 * P * R / (P + R)

Per class (one-vs-rest): for class C, TP = true C predicted C, FP = other predicted C,
FN = true C predicted something else (needs_review counts as a miss for recall, but is
not a false positive for anyone).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .schemas import Prediction

LABELS = config.LABELS
COLS = LABELS + [config.REVIEW]


@dataclass
class Report:
    n: int
    accuracy: float  # needs_review counts as wrong
    accuracy_auto: float  # accuracy on the emails the system DID decide
    coverage: float  # share of emails decided automatically (1 - review rate)
    per_class: dict[str, dict[str, float]]
    macro_f1: float
    matrix: list[list[int]]  # rows = true label, cols = predicted (incl. needs_review)
    jobs_in_spam: int  # the costliest mistake: a real job email filed as spam
    errors: list[tuple[int, str, str, float]]  # (index, true, predicted, confidence)


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def evaluate(truth: list[str], preds: list[Prediction]) -> Report:
    final = [p.label for p in preds]
    n = len(truth)

    per_class: dict[str, dict[str, float]] = {}
    for c in LABELS:
        tp = sum(1 for t, f in zip(truth, final) if t == c and f == c)
        fp = sum(1 for t, f in zip(truth, final) if t != c and f == c)
        fn = sum(1 for t, f in zip(truth, final) if t == c and f != c)
        p, r = _safe_div(tp, tp + fp), _safe_div(tp, tp + fn)
        per_class[c] = {
            "precision": p, "recall": r, "f1": _safe_div(2 * p * r, p + r),
            "support": float(sum(1 for t in truth if t == c)),
        }

    matrix = [[sum(1 for t, f in zip(truth, final) if t == tl and f == pl) for pl in COLS] for tl in LABELS]
    auto = [i for i, f in enumerate(final) if f != config.REVIEW]
    correct_auto = sum(1 for i in auto if final[i] == truth[i])

    return Report(
        n=n,
        accuracy=_safe_div(sum(1 for t, f in zip(truth, final) if t == f), n),
        accuracy_auto=_safe_div(correct_auto, len(auto)),
        coverage=_safe_div(len(auto), n),
        per_class=per_class,
        macro_f1=sum(v["f1"] for v in per_class.values()) / len(LABELS),
        matrix=matrix,
        jobs_in_spam=sum(1 for t, f in zip(truth, final) if t.startswith("job_") and f == "spam"),
        errors=[(i, truth[i], final[i], preds[i].confidence) for i in range(n) if truth[i] != final[i]],
    )


def format_report(r: Report) -> str:
    lines = [f"Emails: {r.n}   Accuracy: {r.accuracy:.1%}   Macro-F1: {r.macro_f1:.3f}"]
    lines.append(
        f"Decided automatically: {r.coverage:.1%}   Accuracy on those: {r.accuracy_auto:.1%}   "
        f"Sent to review: {1 - r.coverage:.1%}"
    )
    lines.append(f"Real job emails filed as SPAM (costliest mistake): {r.jobs_in_spam}")
    lines.append("")
    lines.append(f"{'class':<18}{'precision':>10}{'recall':>9}{'f1':>8}{'support':>9}")
    for c in LABELS:
        m = r.per_class[c]
        lines.append(f"{c:<18}{m['precision']:>10.2f}{m['recall']:>9.2f}{m['f1']:>8.2f}{int(m['support']):>9}")
    lines.append("")
    lines.append("Confusion matrix (rows = TRUE class, columns = PREDICTED):")
    short = [c.replace("job_", "j_")[:12] for c in COLS]
    lines.append(f"{'':<18}" + "".join(f"{s:>13}" for s in short))
    for tl, row in zip(LABELS, r.matrix):
        lines.append(f"{tl:<18}" + "".join(f"{v:>13}" for v in row))
    return "\n".join(lines)


def save_confusion_png(r: Report, path) -> bool:
    """Save the matrix as an image. Returns False if matplotlib isn't installed."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.imshow(r.matrix, cmap="Blues")
    ax.set_xticks(range(len(COLS)), labels=[c.replace("job_", "") for c in COLS], rotation=35, ha="right")
    ax.set_yticks(range(len(LABELS)), labels=[c.replace("job_", "") for c in LABELS])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    for i, row in enumerate(r.matrix):
        for j, v in enumerate(row):
            ax.text(j, i, v, ha="center", va="center", color="white" if v > max(map(max, r.matrix)) / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return True


def threshold_sweep(truth: list[str], preds: list[Prediction], thresholds=None) -> list[dict]:
    """What if we changed the confidence threshold? Re-derive decisions from raw labels.

    Higher threshold -> fewer emails decided automatically (lower coverage) but the ones
    that ARE decided are more often right (higher precision). That is the trade-off.
    """
    thresholds = thresholds or [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    rows = []
    for t in thresholds:
        decided = [(tr, p.raw_label) for tr, p in zip(truth, preds)
                   if p.raw_label in LABELS and p.confidence >= t]
        correct = sum(1 for tr, rl in decided if tr == rl)
        rows.append(
            {
                "threshold": t,
                "coverage": _safe_div(len(decided), len(truth)),
                "accuracy_on_decided": _safe_div(correct, len(decided)),
                "jobs_in_spam": sum(1 for tr, rl in decided if tr.startswith("job_") and rl == "spam"),
            }
        )
    return rows
