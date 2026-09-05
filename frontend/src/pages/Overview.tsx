import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/api/client";
import { KpiTile } from "@/components/common/KpiTile";
import { LoadingState, ErrorState } from "@/components/common/States";
import { ActionBadge, RiskLevelBadge } from "@/components/common/RiskBadge";
import {
  formatCurrencyShort,
  formatDateTime,
  formatNumber,
  formatPercent,
} from "@/components/common/format";
import type { RiskLevel } from "@/api/types";

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: "#16a34a",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#dc2626",
};

export function Overview() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["overview"],
    queryFn: () => api.overview(),
    refetchInterval: 15_000,
  });

  if (isLoading) return <LoadingState label="Loading dashboard…" />;
  if (isError || !data)
    return <ErrorState title="Could not load overview" detail={String(error)} />;

  const riskDistData = (["LOW", "MEDIUM", "HIGH", "CRITICAL"] as RiskLevel[]).map((l) => ({
    level: l,
    count: data.risk_level_distribution[l] ?? 0,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Overview"
        subtitle="Live payment risk operations — computed from your ledger."
      />

      <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <KpiTile label="Live transactions" value={formatNumber(data.live_transactions)} hint={`${formatNumber(data.total_transactions)} total`} />
        <KpiTile
          label="Scored investigations"
          value={formatNumber(data.scored_transactions)}
          hint="ML + evidence engine"
        />
        <KpiTile
          label="High risk"
          value={formatNumber(data.high_count)}
          accent={data.high_count > 0 ? "warn" : "default"}
        />
        <KpiTile
          label="Critical risk"
          value={formatNumber(data.critical_count)}
          accent={data.critical_count > 0 ? "danger" : "default"}
        />
        <KpiTile
          label="Review queue"
          value={formatNumber(data.review_queue_count)}
          hint="Manual review + hold + step-up"
        />
        <KpiTile
          label="Model FP cost (test)"
          value={data.model.expected_business_cost !== undefined
            ? formatCurrencyShort(data.model.expected_business_cost)
            : "—"}
          hint="on held-out test set"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="card xl:col-span-2">
          <div className="card-header">
            <div>
              <div className="card-title">Risk distribution (scored investigations)</div>
              <div className="card-subtitle">Live transactions by risk band</div>
            </div>
          </div>
          <div className="h-64 px-2 pb-4 pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <XAxis dataKey="level" stroke="#5c6b7d" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#5c6b7d" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "#151c25",
                    border: "1px solid #25313f",
                    borderRadius: 6,
                    color: "#e8edf2",
                    fontSize: 12,
                  }}
                  cursor={{ fill: "rgba(37,49,63,0.5)" }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskDistData.map((d) => (
                    <Cell key={d.level} fill={RISK_COLORS[d.level]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Model health</div>
              <div className="card-subtitle">
                {data.model.model_version} · {data.model.model_kind}
              </div>
            </div>
          </div>
          {data.model.available ? (
            <div className="grid grid-cols-2 gap-3 p-4">
              <MetricLine label="Precision" value={formatPercent(data.model.precision)} />
              <MetricLine label="Recall" value={formatPercent(data.model.recall)} />
              <MetricLine label="F1" value={formatPercent(data.model.f1)} />
              <MetricLine label="PR-AUC" value={formatPercent(data.model.pr_auc)} />
              <MetricLine label="FPR" value={formatPercent(data.model.fpr, 2)} />
              <MetricLine label="FNR" value={formatPercent(data.model.fnr, 2)} />
              <div className="col-span-2 rounded-md border border-ink-700/60 bg-ink-800/40 p-2 text-2xs text-ink-400">
                Metrics computed on the <span className="text-ink-200">held-out test set</span>.
                Synthetic dataset — not a claim about production performance.
              </div>
            </div>
          ) : (
            <div className="p-4 text-sm text-ink-400">Metrics unavailable. Train the model first.</div>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Recent investigations</div>
            <div className="card-subtitle">Latest scored transactions</div>
          </div>
          <Link to="/investigations" className="text-xs text-brand-500 hover:underline">
            View all →
          </Link>
        </div>
        {data.recent_investigations.length === 0 ? (
          <div className="p-6 text-sm text-ink-400">
            No scored transactions yet. POST to <code className="rounded bg-ink-800 px-1.5 py-0.5 text-2xs">/api/v1/transactions/score</code> to seed the queue.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700/60 text-2xs uppercase tracking-wider text-ink-400">
                  <th className="px-4 py-2 text-left font-medium">Transaction</th>
                  <th className="px-4 py-2 text-left font-medium">Customer</th>
                  <th className="px-4 py-2 text-right font-medium">Amount</th>
                  <th className="px-4 py-2 text-right font-medium">Score</th>
                  <th className="px-4 py-2 text-left font-medium">Level</th>
                  <th className="px-4 py-2 text-left font-medium">Action</th>
                  <th className="px-4 py-2 text-left font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_investigations.map((r) => (
                  <tr
                    key={r.tx_id}
                    className="border-b border-ink-800/70 last:border-0 hover:bg-ink-800/40"
                  >
                    <td className="px-4 py-2 font-mono text-xs">
                      <Link to={`/investigations/${encodeURIComponent(r.tx_id)}`} className="text-brand-500 hover:underline">
                        {r.tx_id}
                      </Link>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-ink-300">{r.customer_id}</td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {formatCurrencyShort(r.amount, r.currency)}
                    </td>
                    <td className="px-4 py-2 text-right font-semibold tabular-nums">{r.risk_score}</td>
                    <td className="px-4 py-2"><RiskLevelBadge level={r.risk_level} /></td>
                    <td className="px-4 py-2"><ActionBadge action={r.recommended_action} /></td>
                    <td className="px-4 py-2 text-xs text-ink-400">{formatDateTime(r.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-2xs uppercase tracking-wider text-ink-400">{label}</div>
      <div className="text-lg font-semibold tabular-nums text-ink-100">{value}</div>
    </div>
  );
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div>
      <h1 className="text-xl font-semibold tracking-tight text-ink-100">{title}</h1>
      {subtitle && <p className="mt-0.5 text-sm text-ink-400">{subtitle}</p>}
    </div>
  );
}
