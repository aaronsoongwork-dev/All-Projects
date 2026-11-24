# Job-Seeker Email Classifier

Classifies emails into **5 classes** and sends uncertain ones to a **human review** bucket:

| class | meaning |
|---|---|
| `spam` | junk, scams, phishing, fake "jobs" that ask for a fee |
| `job_offer` | a real offer, or a recruiter reaching out about a specific role |
| `job_task` | you must DO something: assessment, documents, pick/confirm a slot (often with a deadline) |
| `job_confirmation` | something is confirmed: application received, interview confirmed, status update |
| `job_rejection` | the employer declines you or closes the role |
| `needs_review` | model confidence below the threshold, or a suspected prompt injection |

It compares a **classic ML baseline** (TF-IDF + logistic regression) against an **LLM few-shot prompt**
on the same labelled test set (F1, latency, cost), and it treats every email as **untrusted input**
(prompt-injection tests, PII redaction).

> All data in this repo is **fake**. Do not commit real emails. `.gitignore` already blocks the usual places.

---

## Quick start (about 10 minutes, no API key needed)

```bash
# 1. open the folder in VS Code, then open a terminal in it
python -m venv .venv

# 2. activate it
#    Windows (PowerShell):  .venv\Scripts\Activate.ps1
#    Windows (cmd):         .venv\Scripts\activate.bat
#    macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # Windows   (macOS/Linux: cp .env.example .env)

python -m emailclf train
python -m emailclf evaluate
python -m pytest -q
```

If `evaluate` prints a table and a confusion matrix, everything works.

---

## Learning path (matches your Day 1 notes)

### Stage 1 (today): classic ML, no API key
| Run | What you learn |
|---|---|
| `python -m emailclf train --show-words` | Training. Cross-validation (K-fold). Which words push towards each class. |
| `python -m emailclf evaluate` | **Confusion matrix**, per-class **precision / recall / F1**. Look at which classes get mixed up. |
| `python -m emailclf sweep` | The **threshold trade-off**: higher threshold = fewer emails decided, but those are more often right. |
| `python -m emailclf evaluate --no-clean` | How much **email cleaning** matters (HTML, quoted replies, signatures). |
| `python -m emailclf rules-report` | How **precise** the cheap rules are. A rule that is wrong is a *confidently* wrong answer. |
| `python -m emailclf classify` | Classify the 6 sample emails in `data/sample_inbox/` (`.txt` and `.eml`). |

Read `emailclf/evaluate.py` (the metrics are written by hand: TP / FP / FN) and `emailclf/cleaning.py`.

### Stage 2: the LLM
1. `pip install anthropic` (or `openai`), then in `.env` set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`
2. `python -m emailclf evaluate --backend llm`
3. `python -m emailclf compare` (baseline vs LLM: F1, latency, tokens/cost)
4. `python -m emailclf sweep --backend llm`, then compare the curve with the baseline's.

Read `emailclf/llm.py` (retries, timeouts, Pydantic validation, retry-with-error) and `emailclf/prompts.py`.

### Stage 3: extras
- `python -m emailclf classify --extract`: pulls company / role / **deadline** / action items as JSON (Pydantic) and prints a deadline list.
- `python -m emailclf inject-test`: prompt-injection attacks against 3 levels of defence.
- `python -m emailclf review`: fix `needs_review` emails by hand; corrections are saved and **used by the next `train`** (feedback loop).

---

## How an email flows through the pipeline

```
raw email
  |  [1] injection scan on RAW text ---- suspicious ---> needs_review   (the LLM never sees it)
  |  [2] clean: strip HTML, quoted replies, signatures, disclaimers, URLs
  |  [3] cheap rules ----------------------- hit ------> label, confidence 1.0 (no model, no cost)
  |  [4] PII redaction (LLM only): emails, phones, card/ID numbers -> [EMAIL] [PHONE] ...
  |  [5] model: TF-IDF baseline  OR  LLM few-shot prompt (JSON validated by Pydantic)
  |  [6] confidence < threshold ---------------------> needs_review
```

## Project layout

```
emailclf/
  config.py       classes, descriptions, threshold, paths, trusted/blocked sender domains
  cleaning.py     HTML / quoted-reply / signature removal
  pii.py          PII redaction
  security.py     prompt-injection detector
  rules.py        cheap high-precision rules
  baseline.py     TF-IDF + logistic regression
  llm.py          LLM clients (mock / anthropic / openai), retries, validation
  prompts.py      all prompt text (naive vs hardened)
  extraction.py   company / role / deadline / action items
  pipeline.py     the flow above
  evaluate.py     metrics, confusion matrix, threshold sweep
  feedback.py     correction loop
  cli.py          the commands
scripts/generate_train_data.py   makes data/train.csv (synthetic)
data/
  test.csv              50 hand-written labelled emails (10 per class)
  train.csv             240 synthetic training emails
  injection_tests.csv   6 prompt-injection attack emails
  sample_inbox/         6 sample files to try `classify`
tests/                   42 tests (cleaning, PII, rules, LLM plumbing, metrics)
```

---

## Results from my run (baseline only, offline)

These are what the code printed when I ran it on the included data. **Your numbers should match closely.**

| Experiment | Accuracy | Macro-F1 | Decided automatically | Accuracy on decided |
|---|---|---|---|---|
| Baseline, cleaning on | 82% | 0.892 | 82% | 100% |
| Baseline, `--no-clean` | 80% | 0.873 | 82% | 97.6% |

Threshold sweep (baseline): at 0.40 it decides 92% of emails at 100% accuracy; at 0.80 it decides only 48%.
Real job emails filed as spam: **0**.

I could **not** run the real LLM here (no network access to LLM APIs from my environment). With
`LLM_PROVIDER=mock` the "LLM" is a simple keyword scorer, so `compare` and `inject-test` numbers for the model are
**simulated**. Run Stage 2 with a real key to get real results. Don't quote the mock numbers in an interview.

### Read these results with suspicion (this is good interview material)
- **Tiny test set.** 50 emails means one email = 2 percentage points. Differences of a few points are noise.
- **Synthetic training data.** 5-fold cross-validation on `train.csv` prints ~1.0 because the templates repeat; that is
  *leakage*, not skill. The hand-written `test.csv` is the honest number (92% before the threshold).
- **Confidence means different things for different models.** With stronger regularisation (`C=5`) the baseline's
  probabilities were so cautious that ~40% of emails fell below 0.6. I raised `C` to 20. An LLM's self-reported
  confidence is *not calibrated* either. Always tune the threshold per model with `sweep`.
- **100% accuracy on decided emails** is partly the threshold doing its job: it removed the uncertain ones (review).
  The cost is that a human reads 18% of the inbox.

---

## Concepts you can now explain (Day 1 notes -> where to see them)

| Concept | Where |
|---|---|
| Confusion matrix, precision, recall, F1 | `evaluate` output, `emailclf/evaluate.py`, `tests/test_pipeline_and_eval.py` |
| Costliest mistake (job offer filed as spam) | "Real job emails filed as SPAM" line; `jobs->spam` column in `sweep` |
| Threshold and trade-off | `sweep`; `needs_review`; `pipeline.py` step [6] |
| K-fold cross-validation | `train` (and why it can mislead) |
| Overfitting / leakage | train.csv CV ~1.0 vs honest test.csv |
| Few-shot vs zero-shot prompting | `prompts.py` (`FEW_SHOT`) |
| JSON output + Pydantic validation + retries | `llm.py` (`structured_call`), `schemas.py`, `tests/test_llm.py` |
| Temperature | `temperature=0` in `llm.py` (consistent output) |
| Context window / cost | `MAX_EMAIL_CHARS` truncation; token counts in `compare` |
| Prompt injection | `security.py`, hardened prompt, `inject-test` |
| Hallucination guard | the model may only return a label from the allowed set (Pydantic `Literal`) |

## Experiments for your interview stories
1. **Cleaning ablation**: `evaluate` vs `evaluate --no-clean`. Add more quoted-reply emails to `test.csv` and see the gap grow.
2. **Baseline vs LLM**: `compare`. Which is better per class? Which is cheaper? Is the LLM worth it?
3. **Threshold**: pick a threshold using `sweep` and justify it ("I'd rather review 18% of mail than misfile one offer").
4. **Rules**: `rules-report`. Write a bad rule on purpose and watch it show up in "Wrong rule decisions".
5. **Injection**: `inject-test` with a real model. Which attack still works? Add your own to `data/injection_tests.csv`.
6. **Feedback loop**: `classify` -> `review` -> `train` -> `evaluate`. Did correcting 5 emails help?

## Limitations (say these out loud)
- Test and training data are small and fake. Collect 100+ of your own **anonymised** emails for real numbers.
- Five classes only. Real inboxes have newsletters, receipts, etc. You may want an `other` class (edit `config.py`).
- Cleaning, rules, PII and injection detection are heuristics. They miss things (names and street addresses are **not**
  redacted; polite, keyword-free injections are **not** detected).
- The LLM's confidence is self-reported and uncalibrated. A stronger approach: ask for probabilities per class, or
  measure agreement across several runs.
- No Gmail/IMAP integration on purpose: OAuth setup eats hours. Export emails to `.eml`/`.txt` instead.

## Security and privacy
- `.env` and anything with real emails are git-ignored. Check `git status` before every commit.
- Emails are untrusted input: they are wrapped in `<email>` tags, the model is told they are data, and its output must
  pass Pydantic validation.
- PII redaction runs before text is sent to a third-party API. Local models (Ollama) avoid sending data out at all.

## Troubleshooting
- `ModuleNotFoundError: emailclf`: run commands from the project folder (where this README is) with `python -m emailclf ...`.
- `No trained model`: run `python -m emailclf train` first.
- `Run: pip install anthropic`: install the package for the provider you set in `.env`.
- `model not found` / `invalid parameter`: set `LLM_MODEL` to a current model name from your provider's docs.
  The client sends `temperature=0`; if a model rejects it, delete that argument in `llm.py`.
- PowerShell blocks activation: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- Windows file encoding problems: all files are read/written as UTF-8 already.

## Using your own emails
Put exported `.txt` / `.eml` files in `data/inbox/` (git-ignored) and run
`python -m emailclf classify --input data/inbox`. To evaluate, label them in a CSV with columns
`id,sender,subject,body,label` and pass `--data your.csv`. Keep real emails out of git.
