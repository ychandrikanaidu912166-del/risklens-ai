# RiskLens AI

**Autonomous Payment Risk Intelligence & Investigation Platform.**

RiskLens AI is a student project built for the Razorpay AI Risk Manager
Buildathon. It focuses on **payment fraud / payment risk intelligence** —
detecting suspicious transactions, explaining *why* they are suspicious with
grounded evidence, and recommending an action for a human analyst.

> The dataset is **synthetic**. Nothing in this project is affiliated with,
> connected to, or uses proprietary data from Razorpay. All numbers reported
> below come from the synthetic held-out test set.

---

## What's in this stage (backend risk engine)

- FastAPI backend with typed Pydantic schemas.
- Reproducible synthetic payment dataset generator (~85k rows, ~6% fraud
  base rate, realistic overlap between legitimate and fraudulent behaviour).
- Feature pipeline with **strict past-only** velocity/behaviour windows to
  avoid target leakage.
- ML model: XGBoost primary (auto-falls back to
  `HistGradientBoostingClassifier` if XGBoost is not installed) with an
  **isotonic calibrator** fit on validation.
- Baseline model (Logistic Regression) reported alongside primary.
- Evaluation on a **time-based held-out test split** — never random.
- **Evidence engine** that derives risk factors (and counter-evidence) from
  actual feature values, rule outputs and model contributions.
- Risk fusion producing a **0–100 calibrated risk score** with LOW /
  MEDIUM / HIGH / CRITICAL bands.
- Decision engine that considers score, confidence, amount and evidence
  strength — never score alone.
- SQLite persistence for customers, merchants, devices, transactions,
  investigations and an append-only audit trail.
- Working REST endpoints for scoring, transaction listing, investigation
  retrieval, health and model metrics.
- Unit tests for fusion, decision, and feature leakage.

The frontend, entity graph visualization, analyst-override flow, AI
investigator narrative and other advanced features come in later stages.

---

## Repository layout

```
backend/
  app/
    main.py            FastAPI application, mounts routers
    config.py          pydantic-settings — env-var driven
    api/               health, transactions, investigations, metrics
    db/                SQLAlchemy engine, ORM models, session helpers
    schemas/           Pydantic request/response models
    ml/                features, model wrapper, trainer, evaluator, SHAP
    risk/              behavior, evidence, fusion, decision, engine
    utils/             logging
  data/generate.py     Synthetic dataset generator (seeded, reproducible)
  scripts/             CLI wrappers: generate_data, train_model,
                       evaluate_model, sample_transactions
  artifacts/           Model / calibrator / metrics / DB (gitignored)
  tests/               pytest suite
```

---

## Setup (Windows, macOS, Linux)

Prereqs: **Python 3.10+**.

```powershell
# 1. Clone and enter the project.
git clone <your-fork-url> risklens-ai
cd risklens-ai

# 2. Create a virtual environment.
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# 3. Install dependencies.
pip install -r backend/requirements.txt
```

Run the four commands in order:

```powershell
# a) Generate the synthetic dataset (~85k rows, seeded).
python -m backend.data.generate

# b) Train the ML model, calibrate it, and write metrics.json.
python -m backend.app.ml.train

# c) Seed SQLite with historical transactions and emit sample payloads.
python -m backend.scripts.sample_transactions --seed-db

# d) Run the API.
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.

---

## API surface (this stage)

Base: `http://127.0.0.1:8000/api/v1`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + model version + feature count |
| POST | `/transactions/score` | Score one transaction; returns full `InvestigationResult` |
| GET  | `/transactions` | List scored live transactions (filter by risk_level / action) |
| GET  | `/transactions/{tx_id}` | Raw transaction |
| GET  | `/investigations/{tx_id}` | Full persisted investigation payload |
| GET  | `/metrics/model` | Latest held-out metrics from `metrics.json` |

---

## Held-out test metrics (synthetic dataset)

Reported straight from `backend/artifacts/metrics.json` after training. Do
**not** treat these numbers as claims about production performance:

- Model: XGBoost, isotonic-calibrated on validation.
- Threshold: chosen to keep validation FPR ≤ 1%.
- Business-cost knobs (`fp_cost_per_tx=12`, `fn_cost_per_tx=250`) are
  illustrative and configurable via `.env`.

---

## Design guarantees

1. **No fabricated numbers.** Every metric comes from `sklearn.metrics`
   computed on the held-out split. The evidence engine's `weight` values
   are computed from feature values / rule outcomes / model probability.
2. **No leakage.** Velocity and behavioural-baseline features for a row at
   time `T` use only rows with `ts < T` (unit-tested in
   `backend/tests/test_features_leakage.py`).
3. **ML predicts, the AI investigation layer will only summarize.** In
   this stage no LLM is called; the risk score is fully deterministic and
   reproducible with seed 42. When the AI investigator is added, it will
   receive structured evidence and be forbidden from inventing new facts.
4. **Score alone doesn't decide.** The decision engine gates BLOCK/HOLD on
   confidence and evidence strength; insufficient evidence with a high
   score routes to `MANUAL_REVIEW`.
5. **Reproducible.** `seed=42` end-to-end (data generator, ML training,
   SHAP background).

---

## What's coming next

- AI investigator (Anthropic API, grounded by evidence-id verifier +
  deterministic template fallback that ships without any API key).
- Entity graph (customer ↔ device ↔ IP ↔ merchant) with `networkx`.
- Analyst-override + decision recording API.
- React + Tailwind analyst dashboard.
- Model comparison and drift monitoring.

---

## Security & scope notes

- No PII in the synthetic data. IPs are stored as SHA-256 truncated hashes.
- Secrets loaded from environment variables. `.env.example` documents them.
- Nothing offensive-security in scope. Defensive risk analytics only.
