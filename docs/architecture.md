# RiskLens AI - Architecture & System Design

RiskLens AI is an end-to-end payment risk intelligence and investigation platform engineered for high-throughput, low-latency fintech environments (such as the Razorpay AI Risk Manager challenge).

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

## High-Level Architecture

```
                                  [ Incoming Transaction Payload ]
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Pydantic Validation  │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                         ┌─────────────────────────────────────────────┐
                         │  Time-Aware Feature Engineering Pipeline    │
                         └──────────────────────┬──────────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
    ┌─────────────────────────┐                                   ┌─────────────────────────┐
    │   Supervised ML Model   │                                   │ Behavioural Baseline    │
    │  (XGBoost Classifier)   │                                   │ (Empirical IQR & Ratio) │
    └────────────┬────────────┘                                   └────────────┬────────────┘
                 │ (Probability & SHAP contribs)                               │ (Anomalies & Baselines)
                 └──────────────────────────────┬──────────────────────────────┘
                                                ▼
                                    ┌───────────────────────┐
                                    │  Risk Fusion Engine   │
                                    │ (0-100 Score & Level) │
                                    └───────────┬───────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
    ┌─────────────────────────┐                                   ┌─────────────────────────┐
    │     Evidence Engine     │                                   │ Counter-Evidence Engine │
    │   (Structured Proof)    │                                   │ (Legitimate Mitigators) │
    └────────────┬────────────┘                                   └────────────┬────────────┘
                 │                                                             │
                 └──────────────────────────────┬──────────────────────────────┘
                                                ▼
                                    ┌───────────────────────┐
                                    │ Entity Graph Engine   │
                                    │ (Device/IP Syndicates)│
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ AI Investigation Hub  │
                                    │ (Gemini / Local Fall) │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ Decision Engine       │
                                    │ (Policy Guardrails)   │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ Analyst Workbench     │
                                    │ & Immutable Audit Log │
                                    └───────────────────────┘
```

---

## Detailed Components

### 1. Data Pipeline (`data/generate_transactions.py`)
- Generates reproducible, realistic payment transactions with seed fixed (`42`).
- Models customer personas (budget, middle, affluent), realistic merchant categories (e-commerce, electronics, gaming, luxury), and temporal dynamics across 60 days.
- Injects subtle, non-trivial fraud scenarios:
  - Account Takeover (ATO)
  - Micro-deposit probing
  - Velocity bursts
  - Cross-account device syndicates
  - Realistic benign edge cases (legitimate high-ticket purchases, foreign travel from known devices).

### 2. Feature Engineering (`ml/features/feature_pipeline.py`)
- Calculates time-aware behavioral ratios:
  - `amount_to_avg_ratio`: Ratio against historical spend
  - `amount_to_max_ratio`: Ratio against maximum prior spend
  - `amount_deviation`: Absolute INR divergence
  - Velocity metrics: `transactions_last_10m`, `transactions_last_1h`, `transactions_last_24h`
  - Temporal cyclic features: `hour_sin`, `hour_cos`
  - Categorical novelty: `is_new_device`, `is_new_country`, `is_unusual_hour`.

### 3. Machine Learning Subsystem (`ml/models/`)
- Compares Logistic Regression baseline against an XGBoost primary model.
- Time-aware chronological 80/20 train/test split preventing future leakage.
- Cost-optimal threshold optimization minimizing:
  `Expected Loss = (FP × ₹250) + (FN × ₹3,500)`

### 4. Behavioural Intelligence (`backend/app/risk_engine/behaviour.py`)
- Computes empirical distributions per customer (mean, median, p95, active hours, known devices, known countries).
- Compares current transaction against customer's own baseline, emitting calibrated anomaly signals with exact values.

### 5. Evidence & Counter-Evidence Engines (`backend/app/risk_engine/`)
- **EvidenceEngine**: Emits verifiable, structured proof items (`AMOUNT_ANOMALY`, `HIGH_VELOCITY`, `NEW_DEVICE`, `NEW_COUNTRY`, `UNUSUAL_HOUR`, `ML_HIGH_RISK`).
- **CounterEvidenceEngine**: Actively searches for reasons why the transaction may be legitimate (`KNOWN_DEVICE`, `KNOWN_COUNTRY`, `NORMAL_AMOUNT`, `ESTABLISHED_ACCOUNT`, `NORMAL_HOUR`, `NORMAL_VELOCITY`), preventing false-positive over-blocking.

### 6. Entity Intelligence (`backend/app/risk_engine/entity_graph.py`)
- In-memory graph linking Customers, Devices, IPs, Merchants, and Transactions.
- Discovers multi-accounting rings where one hardware fingerprint is recycled across unrelated customer accounts.

### 7. Risk Fusion Engine (`backend/app/risk_engine/fusion.py`)
- Transparently combines ML probabilities, behavioral deviations, velocity bursts, and entity graph links.
- Sum of individual factor contributions equals the 0-100 score.
- Calibrates risk levels: `LOW` (0-29), `MEDIUM` (30-59), `HIGH` (60-84), `CRITICAL` (85-100).

### 8. AI Investigator (`backend/app/investigation/ai_investigator.py`)
- Provides human-readable case synthesis grounded entirely in structured evidence.
- Dual-mode architecture:
  - If `GEMINI_API_KEY` is present: Queries Gemini 1.5 Flash with strict JSON schema.
  - If unset or offline: Executes the explainable local deterministic rule engine. Never invents facts or hallucinates.

### 9. Decision Engine & Policy (`backend/app/decision_engine/policy.py`)
- Enforces enterprise policy guardrails (`APPROVE`, `VERIFY`, `MANUAL_REVIEW`, `HOLD`, `BLOCK`).
- AI recommendations can never bypass policy rules.

### 10. Analyst Workbench & Audit Trail (`backend/app/audit/service.py`)
- Provides human override capabilities (`APPROVE`, `HOLD`, `BLOCK`, `FALSE_POSITIVE`, `ESCALATE`).
- Records immutable audit logs with timestamp, actor, decision, and policy version.
