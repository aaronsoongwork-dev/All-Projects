"""Classic ML baseline: TF-IDF + Logistic Regression (scikit-learn).

TF-IDF turns text into numbers (how often each word/word-pair appears, down-weighting
words that appear everywhere). Logistic Regression then learns which words point to which
class and gives a PROBABILITY per class, which is what powers the confidence threshold.

This is cheap, fast, free and runs offline. The LLM has to beat it to be worth its cost.
"""

from __future__ import annotations

import time
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from . import config
from .schemas import Prediction


def _make_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)),
            # class_weight="balanced" stops a big class from drowning out a small one
            # C = how much the model is allowed to trust the training data (higher = less
            # regularisation = more confident probabilities). With C=5 the probabilities were
            # so cautious that ~40% of emails fell under the 0.6 threshold. Lesson: a
            # "confidence" number means different things for different models; tune the
            # threshold per model with `python -m emailclf sweep`.
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=20.0)),
        ]
    )


class BaselineClassifier:
    def __init__(self, pipeline: Pipeline) -> None:
        self.pipeline = pipeline

    @classmethod
    def train(cls, texts: list[str], labels: list[str]) -> "BaselineClassifier":
        pipe = _make_pipeline()
        pipe.fit(texts, labels)
        return cls(pipe)

    @staticmethod
    def cross_validate(texts: list[str], labels: list[str], k: int = 5) -> tuple[float, float]:
        """K-fold cross-validation (Day 1 notes): returns (mean macro-F1, std)."""
        folds = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        scores = cross_val_score(_make_pipeline(), texts, labels, cv=folds, scoring="f1_macro")
        return float(scores.mean()), float(scores.std())

    def save(self, path: Path = config.BASELINE_MODEL_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: Path = config.BASELINE_MODEL_PATH) -> "BaselineClassifier":
        if not Path(path).exists():
            raise FileNotFoundError(f"No trained model at {path}. Run:  python -m emailclf train")
        return cls(joblib.load(path))

    def predict(self, text: str) -> Prediction:
        start = time.perf_counter()
        probs = self.pipeline.predict_proba([text])[0]
        classes = list(self.pipeline.classes_)
        best = max(range(len(classes)), key=lambda i: probs[i])
        return Prediction(
            label=classes[best],
            confidence=float(probs[best]),
            source="baseline",
            raw_label=classes[best],
            latency_s=time.perf_counter() - start,
        )

    def top_words(self, label: str, n: int = 10) -> list[tuple[str, float]]:
        """Which words push an email TOWARDS this class? Great for understanding the model."""
        tfidf: TfidfVectorizer = self.pipeline.named_steps["tfidf"]
        clf: LogisticRegression = self.pipeline.named_steps["clf"]
        idx = list(clf.classes_).index(label)
        names = tfidf.get_feature_names_out()
        weights = clf.coef_[idx]
        order = weights.argsort()[::-1][:n]
        return [(str(names[i]), float(weights[i])) for i in order]
