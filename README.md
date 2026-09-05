# RiskLens AI
### AI-Powered Payment Risk Intelligence & Investigation Platform

> **Razorpay AI Risk Manager Challenge Entry**  
> An end-to-end, production-grade payment fraud detection, behavioural baselining, structured evidence, and AI investigation platform.

---

## Core Principle

```
ML detects.
Behavioural intelligence compares.
Evidence verifies.
Entity intelligence correlates.
AI investigates.
Policy controls actions.
Analyst decides.
Audit records.
Evaluation measures.
```

---

## Key Features

1. **Supervised ML Fraud Classifier**:
   - Compares Logistic Regression baseline against an XGBoost primary model.
   - Strictly evaluated on a held-out chronological test set (no future-data leakage).
   - **Precision: 98.0% | Recall: 84.8% | F1: 90.9% | PR-AUC: 0.8648**.
   - Optimizes for asymmetric operational business cost (\( C_{FP} = ₹250 \), \( C_{FN} = ₹3,500 \)), cutting loss exposure by **51.7%** compared to standard baselines.

2. **Customer Behavioural Intelligence**:
   - Computes customer-specific empirical baselines (average, median, interquartile range, active hours, known devices, known countries).
   - Detects mathematical deviations (e.g. Current amount is 5.39x higher than customer average).

3. **Structured Evidence & Counter-Evidence Engines**:
   - Every risk factor is backed by structured, verifiable evidence (`AMOUNT_ANOMALY`, `HIGH_VELOCITY`, `NEW_DEVICE`, `NEW_COUNTRY`, `UNUSUAL_HOUR`, `SHARED_DEVICE_SYNDICATE`).
   - Actively discovers counter-evidence (verified hardware, domestic residency, long account tenure) to mitigate false-positive over-flagging.

4. **Entity Correlation & Syndicate Graph**:
   - Links Customers, Devices, IPs, Merchants, and Transactions.
   - Flags shared device farms and bot proxy infrastructure across unrelated accounts.

5. **AI Investigator (Gemini LLM & Deterministic Fallback)**:
   - Evaluates structured evidence and produces human-readable case summaries with calibrated language.
   - Supports Google Gemini (`GEMINI_API_KEY`) and features an explainable local deterministic rule engine fallback that never hallucinates facts.

6. **Policy Decision Engine**:
   - Translates composite risk scores and evidence quality into enterprise policy actions: `APPROVE`, `VERIFY`, `MANUAL_REVIEW`, `HOLD`, `BLOCK`.
   - AI recommendations can never bypass policy guardrails.

7. **Analyst Workbench & Immutable Audit Trail**:
   - Human-in-the-loop action interface (`APPROVE`, `HOLD`, `BLOCK`, `FALSE_POSITIVE`, `ESCALATE`).
   - Full chronological event timeline and immutable audit logs.

8. **Modern Fintech Console**:
   - Built with React 18, Vite, TypeScript, Tailwind CSS, Recharts, and Lucide icons.

---

## Target Architecture

```
[ Incoming Payment Transaction ]
               │
               ▼
[ 1. Data Validation (Pydantic v2) ]
               │
               ▼
[ 2. Feature Engineering & Customer Baselines ]
               │
       ┌───────┴─────────────────────────┐
       ▼                                 ▼
[ 3. Supervised ML Model ]     [ 4. Behavioural Intelligence ]
  (XGBoost / Random Forest)      (Amount, Velocity, Novelty ratios)
       └───────┬─────────────────────────┘
               ▼
[ 5. Risk Fusion Engine (0-100 Score & Level: LOW, MED, HIGH, CRIT) ]
               │
       ┌───────┴─────────────────────────┐
       ▼                                 ▼
[ 6. Evidence Engine ]         [ 7. Counter-Evidence Engine ]
  (Structured Risk Proof)        (Legitimate Trust Markers)
       └───────┬─────────────────────────┘
               ▼
[ 8. Entity Intelligence Graph & Investigation Timeline ]
  (Customer-Device-IP-Merchant shared infrastructure)
               │
               ▼
[ 9. AI Investigation Service ]
  (Gemini LLM or Transparent Local Deterministic Fallback)
               │
               ▼
[ 10. Policy Decision Engine ]
  (Automated Action: APPROVE / VERIFY / REVIEW / HOLD / BLOCK)
               │
               ▼
[ 11. Human Analyst Workbench & Immutable Audit Trail ]
  (Analyst override: APPROVE / HOLD / BLOCK / FALSE_POSITIVE / ESCALATE)
```

---

## Project Structure

```
risklens-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # Health, Transactions, Investigations, Metrics
│   │   ├── audit/               # Immutable audit logging service
│   │   ├── config/              # Pydantic environment settings
│   │   ├── database/            # SQLAlchemy SQLite ORM & session management
│   │   ├── decision_engine/     # Enterprise policy guardrails
│   │   ├── investigation/       # AI Investigator (Gemini + Local Fallback)
│   │   ├── models/              # ORM models (Transaction, Investigation, Evidence)
│   │   ├── risk_engine/         # Behaviour, Evidence, Counter-Evidence, Entity Graph, Fusion
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   └── services/            # Unified investigation context orchestration
│   └── main.py                  # ASGI application with auto-seeding lifespan
├── data/
│   ├── generate_transactions.py # Realistic synthetic payment transaction generator
│   └── transactions.csv         # 6,500 transaction dataset with non-trivial fraud
├── docs/
│   ├── architecture.md          # In-depth architectural design specification
│   ├── model-evaluation.md      # Detailed held-out ML performance benchmarks
│   └── demo.md                  # 5-minute evaluator demonstration walkthrough
├── frontend/
│   ├── src/
│   │   ├── api/                 # Type-safe API client wrappers
│   │   ├── components/          # RiskScoreGauge, EntityGraphView
│   │   ├── layouts/             # DashboardLayout with sidebar & system health
│   │   ├── pages/               # Overview, InvestigationQueue, InvestigationDetail, ModelMonitoring
│   │   └── types/               # TypeScript data interfaces
│   ├── package.json
│   └── vite.config.ts
├── ml/
│   ├── features/                # Time-aware behavioral feature extraction
│   └── models/
│       ├── artifacts/           # Trained fraud_model.joblib & metrics.json
│       ├── predictor.py         # Real-time inference service
│       └── train.py             # Supervised training & held-out evaluation
├── scripts/
│   └── seed_demo.py             # Database seeder for demo transactions
├── tests/                       # Complete pytest suite (Unit, Integration, E2E)
└── README.md
```

---

## Installation & Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```
*(Optional: Add `GEMINI_API_KEY=your_key` in `.env` to enable Gemini LLM analysis. If left blank, RiskLens AI operates using its deterministic local investigation engine.)*

### 3. Generate Data & Train ML Models
```bash
# Generate synthetic dataset (6,500 transactions, 60 days)
python data/generate_transactions.py

# Train Logistic Regression baseline & XGBoost primary model
python -m ml.models.train
```

### 4. Start Backend Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```
*The backend runs on port 8001 and automatically initializes SQLite database tables and seeds demo investigations.*

### 5. Start Frontend Application
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173` (or the port displayed in terminal).

---

## Running Automated Tests

Run the full backend and integration test suite:
```bash
python -m pytest tests/ -v
```

Build the frontend production package:
```bash
cd frontend
npm run build
```

---

## REST API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health, model version, and AI engine status |
| `POST` | `/api/v1/transactions/score` | Real-time transaction ingestion and scoring |
| `GET` | `/api/v1/investigations` | Paginated investigation queue with risk/status filters |
| `GET` | `/api/v1/investigations/{id}` | Full unified investigation context (evidence, behaviour, graph) |
| `POST` | `/api/v1/investigations/{id}/analyze` | Trigger fresh AI case investigation |
| `POST` | `/api/v1/investigations/{id}/decision` | Submit analyst human-in-the-loop override |
| `GET` | `/api/v1/investigations/{id}/timeline` | Chronological event timeline |
| `GET` | `/api/v1/investigations/{id}/entities` | Cross-entity correlation graph |
| `GET` | `/api/v1/investigations/{id}/evidence` | Incriminating evidence & counter-evidence |
| `GET` | `/api/v1/metrics/overview` | Live operations KPI dashboard |
| `GET` | `/api/v1/metrics/model` | Held-out ML test set evaluation report |

---

## Limitations & Future Work

- **Graph Storage**: In-memory relational entity correlation is implemented for rapid prototype execution. For multi-billion transaction scales, integration with a distributed graph database (e.g. AWS Neptune or Neo4j) can be added.
- **Continuous Feedback Retraining**: Analyst feedback is persisted immutably in `audit_logs` and `investigations`. An automated batch retraining pipeline (e.g., Airflow or Prefect) can consume validated feedback labels periodically.
- **Federated Identity**: Multi-merchant device graph can be expanded using cross-merchant cryptographic identity hashing.
