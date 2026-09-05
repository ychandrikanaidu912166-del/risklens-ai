import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.app.database.session import get_db
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.investigation_service import InvestigationService
from ml.features.feature_pipeline import extract_single_transaction_features
from ml.models.predictor import predictor

router = APIRouter()

PRESETS = [
    {
        "id": "preset_ato",
        "name": "Account Takeover (ATO Attack)",
        "category": "High Risk Attack",
        "description": "Stolen credentials used from unrecognized device hardware with 6.5x spend spike and rapid velocity.",
        "payload": {
            "customer_id": "cust_sim_ato_victim",
            "merchant_id": "merch_002",
            "amount": 48500.0,
            "currency": "INR",
            "device_id": "dev_hacker_proxy_99",
            "ip_address": "185.220.101.45",
            "country": "IN",
            "payment_method": "credit_card",
            "customer_age_days": 180,
            "customer_transaction_count": 22,
            "customer_avg_amount": 3200.0,
            "customer_max_amount": 7500.0,
            "customer_usual_country": "IN",
            "customer_usual_device": "dev_cust_victim_primary",
            "transactions_last_10m": 4,
            "transactions_last_1h": 7,
            "transactions_last_24h": 9,
            "is_new_device": 1,
            "is_new_country": 0,
            "is_unusual_hour": 1,
        }
    },
    {
        "id": "preset_micro_probe",
        "name": "Micro-Deposit Card Probing",
        "category": "Stealthy Fraud",
        "description": "Automated card enumeration bot testing low values (€1-5 / ₹100) from proxy IP clusters.",
        "payload": {
            "customer_id": "cust_0088",
            "merchant_id": "merch_007",
            "amount": 50.0,
            "currency": "INR",
            "device_id": "dev_syndicate_0",
            "ip_address": "45.154.255.12",
            "country": "US",
            "payment_method": "credit_card",
            "customer_age_days": 45,
            "customer_transaction_count": 8,
            "customer_avg_amount": 1800.0,
            "customer_max_amount": 4200.0,
            "customer_usual_country": "IN",
            "customer_usual_device": "dev_cust_0088_phone",
            "transactions_last_10m": 5,
            "transactions_last_1h": 11,
            "transactions_last_24h": 16,
            "is_new_device": 1,
            "is_new_country": 1,
            "is_unusual_hour": 1,
        }
    },
    {
        "id": "preset_shared_syndicate",
        "name": "Shared Device Farm Syndicate",
        "category": "Organized Fraud Ring",
        "description": "Recycled hardware fingerprint (dev_syndicate_1) operating across multiple unrelated customer accounts.",
        "payload": {
            "customer_id": "cust_0145",
            "merchant_id": "merch_001",
            "amount": 28000.0,
            "currency": "INR",
            "device_id": "dev_syndicate_1",
            "ip_address": "45.154.255.88",
            "country": "IN",
            "payment_method": "net_banking",
            "customer_age_days": 60,
            "customer_transaction_count": 4,
            "customer_avg_amount": 2100.0,
            "customer_max_amount": 3500.0,
            "customer_usual_country": "IN",
            "customer_usual_device": "dev_cust_0145_primary",
            "transactions_last_10m": 3,
            "transactions_last_1h": 6,
            "transactions_last_24h": 8,
            "is_new_device": 1,
            "is_new_country": 0,
            "is_unusual_hour": 0,
        }
    },
    {
        "id": "preset_benign_high_ticket",
        "name": "Legitimate High-Ticket Spend (Benign Anomaly)",
        "category": "False Positive Resistance",
        "description": "High value laptop purchase (₹72,000) from customer's verified phone hardware, domestic IP, with 2+ years tenure.",
        "payload": {
            "customer_id": "cust_0005",
            "merchant_id": "merch_002",
            "amount": 72000.0,
            "currency": "INR",
            "device_id": "dev_cust_0005_primary",
            "ip_address": "103.21.45.89",
            "country": "IN",
            "payment_method": "credit_card",
            "customer_age_days": 750,
            "customer_transaction_count": 48,
            "customer_avg_amount": 6200.0,
            "customer_max_amount": 25000.0,
            "customer_usual_country": "IN",
            "customer_usual_device": "dev_cust_0005_primary",
            "transactions_last_10m": 0,
            "transactions_last_1h": 1,
            "transactions_last_24h": 1,
            "is_new_device": 0,
            "is_new_country": 0,
            "is_unusual_hour": 0,
        }
    },
    {
        "id": "preset_routine_grocery",
        "name": "Routine Domestic Grocery",
        "category": "Normal Low Risk",
        "description": "Everyday ₹850 UPI transaction at regular local merchant from habitual device and daytime hour.",
        "payload": {
            "customer_id": "cust_0019",
            "merchant_id": "merch_003",
            "amount": 850.0,
            "currency": "INR",
            "device_id": "dev_cust_0019_primary",
            "ip_address": "103.21.112.44",
            "country": "IN",
            "payment_method": "upi",
            "customer_age_days": 340,
            "customer_transaction_count": 35,
            "customer_avg_amount": 950.0,
            "customer_max_amount": 2800.0,
            "customer_usual_country": "IN",
            "customer_usual_device": "dev_cust_0019_primary",
            "transactions_last_10m": 0,
            "transactions_last_1h": 0,
            "transactions_last_24h": 1,
            "is_new_device": 0,
            "is_new_country": 0,
            "is_unusual_hour": 0,
        }
    },
]


@router.get("/transactions/simulation/presets")
def get_simulation_presets():
    """Returns realistic transaction presets for live analyst simulation testing."""
    return {"presets": PRESETS}


@router.post("/transactions/simulate")
def simulate_transaction_flow(
    payload: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Executes the REAL backend pipeline step-by-step for a simulated transaction.
    No fake frontend logic; records transaction in SQLite and returns the full pipeline trace.
    """
    tx_dict = payload.model_dump()
    if not tx_dict.get("transaction_id") or tx_dict.get("transaction_id") == "txn_sim_auto":
        tx_dict["transaction_id"] = f"txn_sim_{uuid.uuid4().hex[:8]}"

    if not tx_dict.get("timestamp"):
        tx_dict["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Step 1: Feature Extraction
    features_df = extract_single_transaction_features(tx_dict)
    extracted_features = features_df.iloc[0].to_dict()

    # Step 2: Full pipeline execution via InvestigationService
    result = InvestigationService.score_and_process_transaction(tx_dict, db)

    # Step 3: Fetch full context for UI display
    context = InvestigationService.get_investigation_context(tx_dict["transaction_id"], db)

    # Step 4: Assemble step-by-step pipeline trace
    pipeline_trace = [
        {
            "step": 1,
            "title": "Data Ingestion & Validation",
            "status": "PASSED",
            "detail": f"Validated payload: {tx_dict['currency']} {tx_dict['amount']:,.2f} initiated by {tx_dict['customer_id']}.",
        },
        {
            "step": 2,
            "title": "Time-Aware Feature Engineering",
            "status": "COMPLETED",
            "detail": f"Extracted 17 features: Amount ratio {extracted_features.get('amount_to_avg_ratio', 1.0):.2f}x, Velocity 10m: {extracted_features.get('transactions_last_10m', 0)}.",
        },
        {
            "step": 3,
            "title": "Supervised ML Scoring (XGBoost)",
            "status": "EVALUATED",
            "detail": f"ML Model {predictor.model_version} estimated fraud probability: {result['ml_probability']*100:.1f}%.",
        },
        {
            "step": 4,
            "title": "Behavioral & Anomaly Deviations",
            "status": "EVALUATED",
            "detail": context["customer_behaviour"]["amount_comparison"]["summary"] if context else "Behavior compared.",
        },
        {
            "step": 5,
            "title": "Risk Fusion Engine",
            "status": "FUSED",
            "detail": f"Fused composite risk score: {result['risk_score']}/100 ({result['risk_level']}). Factor contributions: {len(result['factors'])}.",
        },
        {
            "step": 6,
            "title": "Evidence & Counter-Evidence",
            "status": "COMPILED",
            "detail": f"Generated {result['evidence_count']} risk evidence items against {result['counter_evidence_count']} counter-evidence trust markers.",
        },
        {
            "step": 7,
            "title": "Confidence & Business Impact",
            "status": "ANALYZED",
            "detail": f"Confidence: {int(result.get('confidence_score', 0.85)*100)}% ({result.get('evidence_strength', 'MODERATE')} evidence). Risk-adjusted loss: ₹{result.get('business_impact', {}).get('risk_adjusted_exposure', 0):,.2f}.",
        },
        {
            "step": 8,
            "title": "Enterprise Policy Decision",
            "status": "DECIDED",
            "detail": f"Final Policy Action: {result['decision']}. {result.get('business_impact', {}).get('decision_cost_rationale', '')}",
        },
    ]

    return {
        "status": "success",
        "transaction_id": tx_dict["transaction_id"],
        "pipeline_trace": pipeline_trace,
        "result": result,
        "context": context,
    }
