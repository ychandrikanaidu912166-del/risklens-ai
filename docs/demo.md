# RiskLens AI - 5-Minute Interactive Demo Script

This script provides an interactive, end-to-end demonstration of RiskLens AI for evaluators and challenge reviewers.

---

## Prerequisites & Quick Startup

1. **Start Backend Server**:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
   ```

2. **Start Frontend Client**:
   ```bash
   cd frontend
   npm run dev
   # Open browser at http://localhost:5173 (or port shown in terminal)
   ```

3. **Verify Database Status**:
   - Seed script has automatically populated representative transactions.
   - You can re-seed at any time by running:
     ```bash
     python scripts/seed_demo.py
     ```

---

## 5-Minute Walkthrough Flow

### Step 1: Operations Dashboard (`/`)
- Open the dashboard at `http://localhost:5173/`.
- Observe **Live KPI Cards**:
  - Total Ingested Transactions (~350)
  - Active Review Queue
  - High & Critical Risk count
  - Total Financial Loss Exposure
- Review the **Held-Out Supervised ML Performance Banner**:
  - Precision: **98.0%**
  - Recall: **84.8%**
  - F1 Score: **90.9%**
  - PR-AUC: **0.8648**
- Observe the **Risk Score Distribution** chart (Low, Medium, High, Critical).

---

### Step 2: Open a High-Risk Transaction (`/investigations`)
- Navigate to the **Investigation Queue** tab in the sidebar.
- Filter by `Risk Level: Critical` or search for `txn_000653` or `txn_unit_test_999`.
- Click **Investigate** on `txn_unit_test_999` (or `txn_000653`).

---

### Step 3: Flagship Investigation Workbench (`/investigations/:id`)
1. **Header Gauge**:
   - Point out the 0-100 Risk Score circular gauge (e.g. 95/100 CRITICAL).
   - Point out the automated policy recommendation: `BLOCK` or `HOLD`.
2. **"Why is this transaction risky?"**:
   - Show the transparent factor breakdown.
   - Point out exact point contributions:
     - Machine Learning model contribution (+35 pts)
     - Spend Amount Anomaly (+25 pts)
     - Geolocation / Country Discrepancy (+15 pts)
     - Hardware Fingerprint Novelty (+10 pts)
3. **Customer Behaviour Baseline**:
   - Show empirical comparison cards:
     - Amount ratio (e.g. **16.8x** historical average)
     - Hardware device vs verified profile devices
     - Country vs usual domestic location
     - Velocity burst in 10 minutes
4. **Structured Evidence & Counter-Evidence**:
   - Show how each signal links to concrete observed values vs baseline values.
   - Highlight counter-evidence indicators that prevent false-positive over-flagging.
5. **Entity Correlation Map**:
   - Click on the interactive nodes (Transaction, Customer, Device, IP, Merchant).
   - Show shared syndicate links if multiple accounts are associated with the hardware.
6. **Chronological Timeline**:
   - Walk through the event sequence: Session Authentication → Payment Attempt → Risk Scoring → Policy Recommendation.
7. **AI Investigator Workbench**:
   - Read the synthesized narrative.
   - Point out the confidence score (e.g. 94%).
   - Click **"Re-Analyze"** to trigger a real-time fresh analysis.
   - Note the provider badge (`local_deterministic_engine` or `gemini-1.5-flash`).

---

### Step 4: Human-in-the-Loop Analyst Override
- In the **Analyst Decision Workbench** panel on the right:
- Select an action: `HOLD`, `BLOCK`, or `FALSE_POSITIVE`.
- Enter an analyst note:
  > *"Contacted customer via registered mobile number. Confirmed overseas card testing attempt. Block card and freeze account."*
- Click **Submit Decision**.
- Notice:
  - Immediate confirmation banner.
  - Investigation status updates to `RESOLVED`.
  - Timeline adds the signed `ANALYST_DECISION` event.
  - Audit trail permanently records the action.

---

### Step 5: Model Monitoring & Cost Optimization (`/model-monitoring`)
- Click **Model Monitoring** in the sidebar.
- Inspect the **Held-Out Confusion Matrix**:
  - True Negatives, False Positives, False Negatives, True Positives.
- Inspect the **Business Cost Analysis**:
  - False positive friction cost (₹250) vs fraud loss (₹3,500).
  - Net savings achieved through threshold calibration (over 51% loss reduction vs baseline).
- Inspect the **Feature Importance Ranking** chart.
