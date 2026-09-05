# RiskLens AI - Product Specification

## 1. Product Mission
RiskLens AI is an autonomous, explainable, defense-only Payment Risk Intelligence and Investigation Platform designed for modern fintech infrastructure (specifically aligned with the Razorpay AI Risk Manager challenge). Its mission is to stop fraudulent and abusive transactions in real-time, protect merchant revenue, minimize legitimate customer checkout friction, and empower human risk analysts with structured evidence, behavioral baselines, and transparent AI case synthesis.

## 2. Razorpay AI Risk Manager Objective
Fintech merchants face an asymmetric operational challenge:
- **False Positives** introduce customer friction, payment abandonment, and brand churn.
- **False Negatives** result in chargeback fees, loss of goods, and network liability.
RiskLens AI bridges quantitative machine learning with qualitative investigation workflows. It guarantees that:
- Every score is mathematically decomposed into factor point contributions.
- Every major risk flag is rooted in structured, empirical evidence.
- Every flagged transaction is paired with counter-evidence to prevent blind blocking.
- Human analysts maintain ultimate decision authority and signed audit logging.

## 3. Core Architecture
RiskLens AI follows a strict separation of concerns:
```
[ Incoming Payment Transaction ]
               │
               ▼
[ Data Validation (Pydantic v2) ]
               │
               ▼
[ Time-Aware Feature Engineering ]
               │
       ┌───────┴─────────────────────────┐
       ▼                                 ▼
[ Supervised ML Classifier ]   [ Behavioral Intelligence ]
  (XGBoost Primary)              (Customer Baseline Deviations)
       └───────┬─────────────────────────┘
               ▼
[ Risk Fusion Engine (0-100 Score & LOW/MED/HIGH/CRIT Level) ]
               │
       ┌───────┴─────────────────────────┐
       ▼                                 ▼
[ Evidence Engine ]            [ Counter-Evidence Engine ]
  (Incriminating Signals)        (Devil's Advocate Trust Markers)
       └───────┬─────────────────────────┘
               ▼
[ Entity Graph Engine (Shared Devices & IP Syndicates) ]
               │
               ▼
[ AI Investigation Synthesizer (Gemini / Local Fallback) ]
               │
               ▼
[ Decision Policy Engine (Confidence & Business Loss Aware) ]
               │
               ▼
[ Analyst Workbench & Immutable Audit Trail ]
```

## 4. Data Flow & Transaction Lifecycle
1. **Ingestion & Validation**: Payload enters via `POST /api/v1/transactions/score` or `POST /api/v1/transactions/simulate`. Pydantic v2 validates types, constraints, and ranges.
2. **Feature Extraction**: Real-time extraction of 17 time-aware features (amount ratio to mean/median/max, velocity windows, cyclic hour features, device/country novelty).
3. **ML Scoring**: Calibrated inference via trained XGBoost classifier producing continuous fraud probability $p \in [0.0, 1.0]$.
4. **Behavioral Profiling**: Customer empirical baseline calculated dynamically from preceding history ($t_{hist} < t$).
5. **Evidence Generation**: Incriminating signals emit structured `EvidenceItem` records with observed vs baseline values.
6. **Counter-Evidence Generation**: Legitimate indicators emit `CounterEvidenceItem` records that reduce risk and adjust confidence.
7. **Entity Correlation**: In-memory relational graph updates relationships (Customer, Device, IP, Merchant, Account) and identifies shared hardware clusters.
8. **Risk Fusion**: Factors are weighted and fused into a bounded 0-100 score where individual contributions sum to the total.
9. **AI Case Investigation**: 10-point structured assessment generated via Gemini LLM or the deterministic local fallback engine.
10. **Policy Enforcement**: Guardrails evaluate risk score, confidence, and business loss impact to emit automated recommendations.
11. **Human Decision & Audit**: Analyst reviews the workbench, submits override with justification, and writes an immutable audit record.

## 5. Machine Learning Pipeline
- **Dataset**: Reproducible 6,500-transaction benchmark dataset spanning 60 operating days, 250 customers, and 35 merchants.
- **Algorithms**:
  - Baseline: Logistic Regression with balanced class weights.
  - Primary: XGBoost Classifier with scale_pos_weight calibration and tree depth tuning.
- **Split Strategy**: Chronological 80/20 train/test split. Zero future-data leakage.
- **Held-Out Test Results**:
  - Precision: **98.0%**
  - Recall: **84.8%**
  - F1 Score: **90.9%**
  - PR-AUC: **0.8648**
  - ROC-AUC: **0.9745**
  - False Positive Rate: **0.08%** (1 FP)
  - False Negative Rate: **15.2%** (9 FN)

## 6. Risk Fusion Logic
The composite score $S \in [0, 100]$ fuses:
- **ML Fraud Probability**: Up to 35 points ($p \times 35$).
- **Spend Amount Anomaly**: Up to 25 points (scaled by ratio over historical average).
- **Velocity Bursts**: Up to 15 points (frequency in 10m/1h windows).
- **Hardware Novelty**: Up to 10 points (unrecognized device hardware fingerprint).
- **Geographic Discrepancy**: Up to 15 points (foreign/unusual jurisdiction).
- **Temporal Anomaly**: Up to 5 points (off-peak active hours).
- **Entity Syndicate Link**: Up to 15 points (shared device/IP clusters).
- **Counter-Evidence Discount**: Up to -20 points (mitigating trust markers).
Calibrated Levels: `LOW` (0-29), `MEDIUM` (30-59), `HIGH` (60-84), `CRITICAL` (85-100).

## 7. Behavioral Intelligence
Computes customer-specific distributions:
- Historical average amount, median amount, minimum, maximum, and 95th percentile.
- Verified hardware device identifiers.
- Registered jurisdictions / countries.
- Active daily transacting hours (08:00 - 23:00).
- Normal velocity rhythm (0-1 transactions per 10m).
All comparisons display actual mathematical figures (e.g., *"Current amount ₹48,000 is 5.39x customer baseline average of ₹8,900"*).

## 8. Entity Intelligence
Analyzes connections across Customer, Device, IP, Merchant, and Transaction:
- Highlights shared hardware: *"Device fingerprint 'dev_syndicate_0' linked to 4 distinct customer accounts with recent chargebacks."*
- Highlights high-density IP clusters: *"IP 45.154.255.x routed payments for multiple accounts within short window."*
- Relationships alone are contextual signals and do not automatically declare fraud.

## 9. Evidence Chain
Every risk factor links directly to a verifiable evidence record:
$$\text{Decision} \rightarrow \text{Risk Score} \rightarrow \text{Risk Factor} \rightarrow \text{Evidence ID} \rightarrow \text{Observed vs Baseline} \rightarrow \text{Entity Link}$$
Evidence severity levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

## 10. Counter-Evidence ("Devil's Advocate")
The system explicitly searches for legitimate signals before drawing conclusions:
- Hardware fingerprint matches customer's registered primary device.
- Payment location matches domestic profile.
- Amount falls within normal interquartile range.
- Account tenure exceeds 90 days with positive successful payment history.
- Normal daytime commercial operating hours.
Counter-evidence provides confidence calibration and prevents false-positive over-blocking.

## 11. AI Investigation Service
Synthesizes structured evidence into a 10-point analyst-friendly brief:
1. Executive Summary
2. Quantitative Risk Assessment
3. Strongest Incriminating Evidence
4. Legitimate Counter-Evidence
5. Customer Behavioral Assessment
6. Entity / Network Correlation Assessment
7. Business Loss Impact
8. Confidence Score & Calibration
9. Recommended Action
10. What Would Change the Recommendation
- Supports Google Gemini 1.5 Flash when `GEMINI_API_KEY` is present.
- Uses an explainable local deterministic rule engine when offline or unkeyed.
- **Strict Rule**: AI never hallucinates or invents transactions, baselines, or entities.

## 12. Decision Engine & Policy Guardrails
Policy enforces:
- **HIGH RISK + HIGH CONFIDENCE + STRONG EVIDENCE** $\rightarrow$ `HOLD` / `BLOCK`
- **MEDIUM RISK** $\rightarrow$ `VERIFY` (Step-up 2FA) or `MANUAL_REVIEW`
- **HIGH RISK + LOW CONFIDENCE** $\rightarrow$ `MANUAL_REVIEW` (*"High risk, but insufficient confidence. Human review required."*)
- **LOW RISK + STRONG NORMAL BEHAVIOR** $\rightarrow$ `APPROVE`
- **Insufficient Evidence Quality** $\rightarrow$ `MANUAL_REVIEW`
AI recommendations can never bypass policy guardrails.

## 13. Human-in-the-Loop Workflow
Analysts can override recommendations using real backend actions:
- `APPROVE`: Clear payment immediately.
- `HOLD`: Temporarily freeze settlement and request out-of-band verification.
- `BLOCK`: Reject payment and flag account for suspension.
- `FALSE_POSITIVE`: Mark benign anomaly for baseline adjustment.
- `ESCALATE`: Route case to Senior Fraud Operations.
Every action requires a justification reason and is immutably signed to the audit log.

## 14. Business-Loss & Cost-Aware Decisioning
Fintech decisions balance asymmetric financial costs:
$$\text{Operational Cost} = (\text{FP} \times ₹250) + (\text{FN} \times ₹3,500)$$
For every transaction, the system computes:
- `transaction_amount`: Gross transaction value.
- `potential_loss_exposure`: Maximum chargeback liability.
- `risk_adjusted_exposure`: $\text{Amount} \times \frac{\text{Risk Score}}{100}$.
- `false_positive_friction_cost`: Estimated customer support and churn cost (₹250).
- `decision_cost_rationale`: Cost justification for the recommended policy action.

## 15. Auditability & Compliance
Immutable records captured for:
- `TRANSACTION_SCORED`
- `INVESTIGATION_CREATED`
- `AI_ANALYSIS_GENERATED`
- `POLICY_RECOMMENDATION`
- `ANALYST_DECISION_RECORDED`
Records include timestamp, actor, entity ID, previous status, and audit parameters.

## 16. Evaluation Methodology
- Rigorous held-out test evaluation.
- Time-aware chronological separation preventing data leakage.
- Metrics reported: Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, FNR, Confusion Matrix, and Expected Operational Cost.

## 17. Security Principles
- **Defense-Only**: No offensive fraud generation, credential stuffing, or exploit capabilities.
- **Zero Secret Exposure**: All API keys and environment variables strictly protected.
- **SQL Injection Prevention**: Parameterized SQLAlchemy ORM queries throughout.
- **Pydantic Validation**: All API inputs and outputs strictly typed and bounds-checked.

## 18. API Structure
- `GET /health`
- `POST /api/v1/transactions/score`
- `POST /api/v1/transactions/simulate`
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`
- `POST /api/v1/investigations/{id}/analyze`
- `POST /api/v1/investigations/{id}/decision`
- `GET /api/v1/investigations/{id}/timeline`
- `GET /api/v1/investigations/{id}/entities`
- `GET /api/v1/investigations/{id}/evidence`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/metrics/model`

## 19. Current Limitations & Scalability
- Relational graph intelligence is optimized for SQLite in this standalone deployment. At multi-million TPS scale, this layer interfaces cleanly with distributed graph engines (e.g., Neo4j or Amazon Neptune).
- Batch retraining triggers can be orchestrated via Prefect or Apache Airflow consuming signed analyst feedback.

## 20. Strict Non-Fabrication Rule
Under no circumstances may metrics, evidence, baselines, or AI conclusions be fabricated or hardcoded. All numbers presented in the UI must originate from actual model artifacts, empirical customer histories, or real backend engine calculations.
