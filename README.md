# RiskLens AI

**Autonomous Payment Risk Intelligence & Investigation Platform.**

RiskLens AI is a student project built for the Razorpay AI Risk Manager
Buildathon. It focuses on **payment fraud / payment risk intelligence** —
detecting suspicious transactions, explaining *why* they are suspicious with
grounded evidence, presenting the case to a human analyst in a professional
dashboard, and recording their decision to an audit trail.

> The dataset is **synthetic**. Nothing in this project is affiliated with,
> connected to, or uses proprietary data from Razorpay. All numbers displayed
> in the dashboard come from the synthetic held-out test set or the live
> in-memory database.

---

## What's inside

### Backend (Stage 1)

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
- **Grounded deterministic AI investigator** — every claim it emits
  references an evidence id produced by the risk engine.
- SQLite persistence with append-only audit trail and analyst decisions.

### Frontend (Stage 2)

- React + Vite + TypeScript + Tailwind CSS analyst dashboard.
- Pages:
  - **Overview** — real KPIs from `/overview`, risk distribution, model
    health tiles from `/metrics/model`, recent investigations table.
  - **Investigation Queue** (`/investigations`) — filterable/sortable table
    of scored transactions from `/transactions`.
  - **Investigation Detail** (`/investigations/:txId`) — risk dial, evidence
    cards, counter-evidence, model SHAP waterfall, customer behaviour
    comparison, timeline, entity graph, AI investigation report and
    analyst decision panel.
  - **Model Monitoring** (`/model-monitoring`) — held-out precision /
    recall / F1 / PR-AUC / ROC-AUC / FPR / FNR / Brier / confusion matrix
    / PR curve / business cost, plus baseline comparison.
  - **Audit Trail** (`/audit`) — append-only event stream.
- Centralised typed API client, React Query for data fetching, loading /
  empty / error states everywhere.

---

## Repository layout

```
backend/
  app/
    main.py            FastAPI application; mounts all routers
    api/               health, overview, transactions, investigations, ai,
                       decisions, audit, entities, metrics
    db/                SQLAlchemy engine, ORM models
    schemas/           Pydantic request/response models
    ml/                features, model wrapper, trainer, evaluator, SHAP
    risk/              behaviour, evidence, fusion, decision, engine
    ai/                deterministic grounded investigator
    utils/             logging, config
  data/generate.py     Synthetic dataset generator (seeded, reproducible)
  scripts/             generate_data, train_model, evaluate_model,
                       sample_transactions, seed_demo
  artifacts/           Model / calibrator / metrics / SQLite (gitignored)
  tests/               pytest suite (13 tests)
frontend/
  package.json         Vite + React + TS + Tailwind + React Query + Recharts
  src/
    api/               Typed API client + type mirrors of backend schemas
    components/
      layout/          Sidebar, topbar, shell
      common/          KpiTile, RiskBadge, ScoreDial, States, format helpers
      investigation/   EvidenceList, ShapWaterfall, BehaviorPanel, Timeline,
                       EntityGraph, AiInvestigation, DecisionPanel
    pages/             Overview, Queue, Investigation, ModelMonitoring, Audit
```

---

## Setup and run (Windows, macOS, Linux)

Prereqs: **Python 3.10+** and **Node 20+**.

### 1. Backend

```powershell
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

pip install -r backend/requirements.txt

python -m backend.data.generate                   # (a) generate synthetic dataset
python -m backend.app.ml.train                    # (b) train ML model, write metrics.json
python -m backend.scripts.sample_transactions --seed-db   # (c) seed SQLite with history
python -m backend.scripts.seed_demo --count 60    # (d) score a mix of live investigations

uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI.

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api/*` to `http://127.0.0.1:8000`,
so the frontend talks to the real FastAPI backend.

### 3. Tests

```powershell
python -m pytest backend/tests -q     # backend  (13 tests)
cd frontend && npm run build          # frontend production build (TS + Vite)
```

---

## API surface consumed by the frontend

Base: `http://127.0.0.1:8000/api/v1`

| Method | Path | Used by |
|---|---|---|
| GET | `/health` | Topbar |
| GET | `/overview` | Overview page |
| GET | `/transactions` | Queue page |
| POST | `/transactions/score` | Programmatic (samples, seed) |
| GET | `/investigations/{tx_id}` | Investigation detail |
| GET | `/investigations/{tx_id}/ai-report` | AI Investigation section |
| GET | `/entities/{type}/{id}/subgraph` | Entity graph |
| POST | `/decisions` | Analyst decision panel |
| GET | `/decisions?tx_id=` | Decision history |
| GET | `/audit` | Audit page |
| GET | `/metrics/model` | Model Monitoring |

Error contract: `{detail: string}` with 4xx for client errors, 5xx for
server. The client centralises this in `frontend/src/api/client.ts`
(`ApiError` class); no URLs live in components.

---

## Analyst decision flow

The Investigation Detail page's decision panel offers five actions:
**APPROVE**, **HOLD**, **BLOCK**, **FALSE POSITIVE**, **ESCALATE**.

Submitting one:
1. `POST /api/v1/decisions` with `{tx_id, action, reason, analyst_id}`.
2. Persists to the `decisions` table.
3. Writes an `ANALYST_DECISION` row to the append-only `audit_events`
   table — visible on the Audit Trail page.
4. **Does not** retrain the model. Feedback is stored as controlled
   evaluation data only.

---

## Held-out test metrics (synthetic dataset)

Reported straight from `backend/artifacts/metrics.json` after training. Do
**not** treat these numbers as claims about production performance:

- Model: XGBoost, isotonic-calibrated on validation.
- Threshold: chosen to keep validation FPR ≤ 1%.
- Business-cost knobs (`fp_cost_per_tx=12`, `fn_cost_per_tx=250`) are
  illustrative and configurable via `.env`.

The Model Monitoring page renders these numbers verbatim from the API —
nothing in the UI is hardcoded.

---

## Design guarantees

1. **No fabricated numbers.** Every metric comes from `sklearn.metrics` on
   a held-out split. Every evidence weight is derived from a feature value,
   rule outcome, or model contribution.
2. **No leakage.** Velocity and behavioural-baseline features for a row at
   time `T` use only rows with `ts < T`
   (unit-tested in `backend/tests/test_features_leakage.py`).
3. **ML predicts, AI narrates.** The deterministic risk engine computes
   the score. The AI investigation layer only summarises evidence the
   engine already produced — it references evidence ids and does not
   introduce facts.
4. **Score alone doesn't decide.** The decision engine gates BLOCK/HOLD on
   confidence and evidence strength; insufficient evidence with a high
   score routes to `MANUAL_REVIEW`.
5. **Reproducible.** `seed=42` end-to-end (data generator, ML training,
   SHAP background, demo seed).

---

## Screenshots

_Placeholder — capture screenshots of the running dashboard and drop them here:_

- `docs/screenshots/overview.png`
- `docs/screenshots/queue.png`
- `docs/screenshots/investigation.png`
- `docs/screenshots/model-monitoring.png`
- `docs/screenshots/audit.png`

---

## Roadmap

- Anthropic-powered AI investigator (behind evidence-id verifier — falls
  back to deterministic template when no API key is set).
- Model drift monitoring (PSI per feature between training and live).
- Docker Compose + Postgres adapter (SQLAlchemy already abstracts it).
- Playwright end-to-end tests for the analyst workflow.

---

## Security & scope notes

- No PII in the synthetic data. IPs are stored as SHA-256 truncated hashes.
- Secrets loaded from environment variables. `.env.example` documents them.
- CORS restricted to configured origins in `RISKLENS_CORS_ORIGINS`.
- No offensive-security functionality. Defensive risk analytics only.
