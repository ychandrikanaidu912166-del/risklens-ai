import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/api/client";
import { KpiTile } from "@/components/common/KpiTile";
import { LoadingState, ErrorState } from "@/components/common/States";
import { formatCurrencyShort, formatNumber, formatPercent } from "@/components/common/format";
import { PageHeader } from "./Overview";

export function ModelMonitoring() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["metrics"],
    queryFn: () => api.metrics(),
  });

  if (isLoading) return <LoadingState label="Loading model metrics…" />;
  if (isError || !data)
    return <ErrorState title="Metrics unavailable" detail={String(error)} />;

  const p = data.primary;
  const b = data.baseline;
  const cm = p.confusion_matrix;

  const prCurveData = p.pr_curve.map((pt) => ({
    recall: Number(pt.recall.toFixed(3)),
    precision: Number(pt.precision.toFixed(3)),
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Model monitoring"
        subtitle="Held-out test set evaluation for the primary classifier."
      />

      <div className="rounded-md border border-ink-700/60 bg-ink-800/40 p-3 text-xs text-ink-300">
        Metrics computed on the <span className="text-ink-100 font-semibold">held-out test split</span>
        &nbsp;of the synthetic payments dataset. These numbers describe this model on
        this dataset — they do not imply production performance.
      </div>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-6">
        <KpiTile label="Precision" value={formatPercent(p.precision)} accent="good" />
        <KpiTile label="Recall" value={formatPercent(p.recall)} />
        <KpiTile label="F1" value={formatPercent(p.f1)} />
        <KpiTile label="PR-AUC" value={formatPercent(p.pr_auc)} />
        <KpiTile label="ROC-AUC" value={formatPercent(p.roc_auc)} />
        <KpiTile label="Brier" value={p.brier.toFixed(4)} hint="calibration loss (lower better)" />
        <KpiTile label="FPR" value={formatPercent(p.fpr, 2)} accent={p.fpr > 0.05 ? "warn" : "default"} />
        <KpiTile label="FNR" value={formatPercent(p.fnr, 2)} />
        <KpiTile label="Threshold" value={p.threshold.toFixed(3)} hint="operating point" />
        <KpiTile label="FP cost" value={formatCurrencyShort(p.business_cost.false_positive_cost)} />
        <KpiTile label="FN cost" value={formatCurrencyShort(p.business_cost.false_negative_cost)} />
        <KpiTile
          label="Expected business cost"
          value={formatCurrencyShort(p.business_cost.expected_business_cost)}
          accent="warn"
          hint={`FP=${p.business_cost.fp_cost_per_tx} / tx · FN=${p.business_cost.fn_cost_per_tx} / tx`}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="card p-4">
          <div className="mb-3">
            <div className="card-title">Confusion matrix (test)</div>
            <div className="card-subtitle">Predictions at operating threshold {p.threshold.toFixed(3)}</div>
          </div>
          <div className="grid grid-cols-3 items-stretch gap-2 text-center text-sm">
            <div />
            <div className="text-2xs uppercase tracking-wider text-ink-400">Pred: Legit</div>
            <div className="text-2xs uppercase tracking-wider text-ink-400">Pred: Fraud</div>
            <div className="text-2xs uppercase tracking-wider text-ink-400 self-center">Actual: Legit</div>
            <CmCell label="TN" value={cm.tn} tone="good" />
            <CmCell label="FP" value={cm.fp} tone="warn" />
            <div className="text-2xs uppercase tracking-wider text-ink-400 self-center">Actual: Fraud</div>
            <CmCell label="FN" value={cm.fn} tone="danger" />
            <CmCell label="TP" value={cm.tp} tone="good" />
          </div>
        </div>

        <div className="card p-4">
          <div className="mb-3">
            <div className="card-title">Precision–Recall curve (test)</div>
            <div className="card-subtitle">Model separability across thresholds</div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={prCurveData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid stroke="#25313f" strokeDasharray="2 3" />
                <XAxis dataKey="recall" stroke="#5c6b7d" fontSize={11} domain={[0, 1]} type="number" tickFormatter={(v) => v.toFixed(1)} />
                <YAxis dataKey="precision" stroke="#5c6b7d" fontSize={11} domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
                <Tooltip contentStyle={{ background: "#151c25", border: "1px solid #25313f", borderRadius: 6, color: "#e8edf2", fontSize: 12 }} />
                <Line type="monotone" dataKey="precision" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="card p-4">
        <div className="mb-3">
          <div className="card-title">Baseline comparison</div>
          <div className="card-subtitle">Logistic regression trained on the same features.</div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-700/60 text-2xs uppercase tracking-wider text-ink-400">
                <th className="px-4 py-2 text-left">Model</th>
                <th className="px-4 py-2 text-right">Precision</th>
                <th className="px-4 py-2 text-right">Recall</th>
                <th className="px-4 py-2 text-right">F1</th>
                <th className="px-4 py-2 text-right">PR-AUC</th>
                <th className="px-4 py-2 text-right">ROC-AUC</th>
                <th className="px-4 py-2 text-right">FPR</th>
                <th className="px-4 py-2 text-right">FNR</th>
              </tr>
            </thead>
            <tbody>
              <ComparisonRow name={`Primary · ${data.model_kind}`} m={p} highlight />
              <ComparisonRow name="Baseline · logistic regression" m={b} />
            </tbody>
          </table>
        </div>
      </section>

      <section className="card p-4">
        <div className="mb-2 card-title">Dataset</div>
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
          <MiniStat label="Model version" value={data.model_version} />
          <MiniStat label="Fraud rate" value={formatPercent(data.fraud_rate, 2)} />
          <MiniStat label="Train rows" value={formatNumber(data.split_sizes.train)} />
          <MiniStat label="Val rows" value={formatNumber(data.split_sizes.val)} />
          <MiniStat label="Test rows" value={formatNumber(data.split_sizes.test)} />
          <MiniStat label="Total rows" value={formatNumber(data.dataset_rows)} />
          <MiniStat label="Features" value={formatNumber(data.feature_columns.length)} />
          <MiniStat label="Generated at" value={new Date(data.generated_at).toLocaleString()} />
        </div>
      </section>
    </div>
  );
}

function CmCell({ label, value, tone }: { label: string; value: number; tone: "good" | "warn" | "danger" }) {
  const toneClass =
    tone === "good"
      ? "bg-risk-low/10 text-risk-low ring-risk-low/30"
      : tone === "warn"
      ? "bg-risk-high/10 text-risk-high ring-risk-high/30"
      : "bg-risk-critical/10 text-risk-critical ring-risk-critical/30";
  return (
    <div className={`rounded-md ring-1 ring-inset p-3 ${toneClass}`}>
      <div className="text-2xs uppercase tracking-wider opacity-80">{label}</div>
      <div className="mt-0.5 text-2xl font-semibold tabular-nums">{formatNumber(value)}</div>
    </div>
  );
}

function ComparisonRow({ name, m, highlight }: { name: string; m: import("@/api/types").PrimaryMetrics; highlight?: boolean }) {
  return (
    <tr className={`border-b border-ink-800/70 last:border-0 ${highlight ? "bg-ink-800/30" : ""}`}>
      <td className="px-4 py-2 text-ink-100">{name}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.precision)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.recall)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.f1)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.pr_auc)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.roc_auc)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.fpr, 2)}</td>
      <td className="px-4 py-2 text-right tabular-nums">{formatPercent(m.fnr, 2)}</td>
    </tr>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-ink-700/60 bg-ink-800/40 p-2">
      <div className="text-2xs uppercase tracking-wider text-ink-400">{label}</div>
      <div className="mt-0.5 text-sm text-ink-100 tabular-nums">{value}</div>
    </div>
  );
}
