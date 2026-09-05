# RiskLens AI — Instructions for Future Coding Agents

> **CRITICAL DIRECTIVE FOR ALL AGENTS WORKING ON THIS REPOSITORY:**
>
> 1. **Read `docs/RISKLENS_PRODUCT_SPEC.md` before making any architectural or algorithmic changes.**
> 2. **Preserve existing verified functionality.** Do not destroy, rewrite, or break working APIs, database schemas, ML models, or tests.
> 3. **Never fabricate metrics, evidence, transaction histories, or AI outputs.** All evaluations must be mathematically grounded in real model artifacts and empirical database records.
> 4. **Defense-only posture.** Do not implement offensive attack tools, credential harvesting, or unauthorized exploit generation.
> 5. **Prefer incremental, tested changes.** After modifying any backend or ML code, run `python -m pytest tests/ -v`. After modifying any frontend code, run `npm run build` in `frontend/`.
> 6. **Do not introduce unnecessary infrastructure** (such as Redis, Neo4j, or external cloud dependencies) unless specifically requested by the user.

---

## Architecture Summary
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy (SQLite `risklens.db`).
- **ML Subsystem**: scikit-learn, XGBoost (`v1.2.0-xgb`), SHAP, Pandas, NumPy.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide icons, Recharts.
- **AI Investigation**: Google Gemini 1.5 Flash (via `GEMINI_API_KEY`) with automatic local deterministic rule engine fallback.

## Quick Commands
- Run backend tests: `python -m pytest tests/ -v`
- Start backend: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001`
- Build frontend: `cd frontend && npm run build`
- Start frontend: `cd frontend && npm run dev`
