import React, { useEffect, useState } from 'react';
import {
  LineChart,
  ShieldCheck,
  AlertCircle,
  TrendingDown,
  Layers,
  Cpu,
  BarChart3,
  CheckCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { fetchModelMetrics } from '../api/client';

export const ModelMonitoring: React.FC = () => {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModelMetrics()
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm text-slate-400">Loading Held-Out ML Evaluation Metrics...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300">
        <h3 className="font-semibold text-base mb-1">Failed to Load Model Metrics</h3>
        <p className="text-sm">{error || 'Metrics artifact not found.'}</p>
      </div>
    );
  }

  const primary = report.primary_xgboost?.cost_optimal_threshold || {};
  const baseline = report.baseline_logistic_regression || {};
  const cm = primary.confusion_matrix || { tn: 0, fp: 0, fn: 0, tp: 0 };
  const featImp = report.primary_xgboost?.feature_importance || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Model Performance &amp; Evaluation
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-500/15 border border-blue-500/30 text-blue-400">
            {report.model_version}
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Rigorous statistical evaluation strictly evaluated on the held-out test set. No future-data leakage.
        </p>
      </div>

      {/* Held-out Guarantee Notice */}
      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <strong className="text-blue-300 font-semibold block mb-0.5">
            Empirical Validation Guarantee
          </strong>
          All metrics below are computed solely on the held-out test split (
          {report.dataset?.test_transactions.toLocaleString()} transactions, {report.dataset?.test_fraud_count} fraud instances).
          The model does NOT claim 100% accuracy; realistic false positives and false negatives are preserved and managed via policy guardrails.
        </div>
      </div>

      {/* Key Metric Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Precision */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase">Precision</span>
          <div className="text-3xl font-extrabold font-mono text-emerald-400 mt-2">
            {(primary.precision * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Baseline (Logistic Reg): {(baseline.precision * 100).toFixed(1)}%
          </p>
        </div>

        {/* Recall */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase">Recall</span>
          <div className="text-3xl font-extrabold font-mono text-emerald-400 mt-2">
            {(primary.recall * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Baseline (Logistic Reg): {(baseline.recall * 100).toFixed(1)}%
          </p>
        </div>

        {/* F1 Score */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase">F1 Score</span>
          <div className="text-3xl font-extrabold font-mono text-blue-400 mt-2">
            {(primary.f1 * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Baseline (Logistic Reg): {(baseline.f1 * 100).toFixed(1)}%
          </p>
        </div>

        {/* PR-AUC */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase">PR-AUC</span>
          <div className="text-3xl font-extrabold font-mono text-purple-400 mt-2">
            {primary.pr_auc?.toFixed(4)}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            ROC-AUC: {primary.roc_auc?.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Confusion Matrix & Business Cost Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-400" />
              Held-Out Confusion Matrix
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluated at optimal cost-calibrated decision threshold (τ = {primary.threshold}).
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 max-w-md mx-auto my-6 text-center">
            {/* True Negative */}
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
              <span className="text-[11px] font-semibold uppercase text-emerald-400 block">
                True Negatives (TN)
              </span>
              <span className="text-3xl font-extrabold font-mono text-emerald-300 mt-1 block">
                {cm.tn?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-400 mt-1 block">Legitimate Cleared</span>
            </div>

            {/* False Positive */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
              <span className="text-[11px] font-semibold uppercase text-amber-400 block">
                False Positives (FP)
              </span>
              <span className="text-3xl font-extrabold font-mono text-amber-300 mt-1 block">
                {cm.fp?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-400 mt-1 block">Friction / False Flag</span>
            </div>

            {/* False Negative */}
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
              <span className="text-[11px] font-semibold uppercase text-red-400 block">
                False Negatives (FN)
              </span>
              <span className="text-3xl font-extrabold font-mono text-red-300 mt-1 block">
                {cm.fn?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-400 mt-1 block">Missed Fraud Loss</span>
            </div>

            {/* True Positive */}
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
              <span className="text-[11px] font-semibold uppercase text-blue-400 block">
                True Positives (TP)
              </span>
              <span className="text-3xl font-extrabold font-mono text-blue-300 mt-1 block">
                {cm.tp?.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-400 mt-1 block">Fraud Intercepted</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800 text-xs text-slate-400">
            <div>
              <span>False Positive Rate (FPR): </span>
              <strong className="text-slate-200 font-mono font-semibold">
                {(primary.fpr * 100).toFixed(2)}%
              </strong>
            </div>
            <div>
              <span>False Negative Rate (FNR): </span>
              <strong className="text-slate-200 font-mono font-semibold">
                {(primary.fnr * 100).toFixed(1)}%
              </strong>
            </div>
          </div>
        </div>

        {/* Business Cost Analysis */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
              <TrendingDown className="w-5 h-5 text-emerald-400" />
              Expected Business Cost Analysis
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Balancing user friction cost vs unrecovered fraud loss.
            </p>

            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Unit False Positive Cost (Friction/Support):</span>
                  <span className="font-mono text-slate-200 font-bold">
                    ₹{report.business_cost_params?.fp_cost || 250}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Unit False Negative Cost (Fraud Loss):</span>
                  <span className="font-mono text-slate-200 font-bold">
                    ₹{report.business_cost_params?.fn_cost || 3500}
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">XGBoost Total Expected Cost:</span>
                  <span className="font-mono text-emerald-400 font-extrabold text-base">
                    ₹{primary.business_cost?.total_cost?.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Baseline Logistic Reg Cost:</span>
                  <span className="font-mono text-slate-400 font-bold">
                    ₹{baseline.business_cost?.total_cost?.toLocaleString()}
                  </span>
                </div>
                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-emerald-400 font-semibold">
                  <span>Net Loss Reduction vs Baseline:</span>
                  <span className="font-mono">
                    ₹{(baseline.business_cost?.total_cost - primary.business_cost?.total_cost)?.toLocaleString()} saved
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            Decision threshold is calibrated to minimize expected operational loss, not raw accuracy.
          </div>
        </div>
      </div>

      {/* Feature Importance Chart */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <div className="mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            XGBoost Feature Importance Ranking
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized relative contribution of behavioural, velocity, and novelty features.
          </p>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={featImp.slice(0, 8)}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
            >
              <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
              <YAxis
                type="category"
                dataKey="feature"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              />
              <Bar dataKey="importance" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
