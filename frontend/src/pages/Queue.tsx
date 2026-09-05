import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "@/api/client";
import { ActionBadge, RiskLevelBadge } from "@/components/common/RiskBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/common/States";
import { formatCurrencyShort, formatDateTime } from "@/components/common/format";
import { PageHeader } from "./Overview";
import type { Action, RiskLevel, TransactionSummary } from "@/api/types";

const RISK_LEVELS: (RiskLevel | "ALL")[] = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];
const ACTIONS: (Action | "ALL")[] = ["ALL", "APPROVE", "STEP_UP", "MANUAL_REVIEW", "HOLD", "BLOCK"];
type SortKey = "risk_score" | "amount" | "ts";

export function Queue() {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<(typeof RISK_LEVELS)[number]>("ALL");
  const [actionFilter, setActionFilter] = useState<(typeof ACTIONS)[number]>("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("risk_score");
  const [sortDesc, setSortDesc] = useState(true);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["transactions", levelFilter, actionFilter],
    queryFn: () =>
      api.listTransactions({
        risk_level: levelFilter === "ALL" ? undefined : levelFilter,
        action: actionFilter === "ALL" ? undefined : actionFilter,
        limit: 500,
      }),
    refetchInterval: 20_000,
  });

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    let rows: TransactionSummary[] = data;
    if (q) {
      rows = rows.filter(
        (r) =>
          r.tx_id.toLowerCase().includes(q) ||
          r.customer_id.toLowerCase().includes(q) ||
          r.merchant_id.toLowerCase().includes(q),
      );
    }
    const sorted = [...rows].sort((a, b) => {
      const A = sortKey === "risk_score" ? a.risk_score : sortKey === "amount" ? a.amount : new Date(a.ts).getTime();
      const B = sortKey === "risk_score" ? b.risk_score : sortKey === "amount" ? b.amount : new Date(b.ts).getTime();
      return sortDesc ? B - A : A - B;
    });
    return sorted;
  }, [data, search, sortKey, sortDesc]);

  function toggleSort(k: SortKey) {
    if (sortKey === k) setSortDesc((v) => !v);
    else {
      setSortKey(k);
      setSortDesc(true);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Investigation queue"
        subtitle="Scored transactions awaiting analyst review."
      />

      <div className="card">
        <div className="flex flex-wrap items-center gap-3 border-b border-ink-700/60 p-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tx / customer / merchant…"
              className="input pl-8"
            />
          </div>
          <Select
            label="Risk level"
            value={levelFilter}
            onChange={(v) => setLevelFilter(v as typeof levelFilter)}
            options={RISK_LEVELS}
          />
          <Select
            label="Action"
            value={actionFilter}
            onChange={(v) => setActionFilter(v as typeof actionFilter)}
            options={ACTIONS.map((a) => a)}
          />
        </div>

        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <div className="p-4">
            <ErrorState title="Could not load transactions" detail={String(error)} />
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No investigations match"
            detail="Try clearing filters, or POST a transaction to /api/v1/transactions/score."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700/60 text-2xs uppercase tracking-wider text-ink-400">
                  <Th>Transaction</Th>
                  <Th>Customer</Th>
                  <Th>Merchant</Th>
                  <Th align="right" sortable active={sortKey === "amount"} desc={sortDesc} onClick={() => toggleSort("amount")}>Amount</Th>
                  <Th align="right" sortable active={sortKey === "risk_score"} desc={sortDesc} onClick={() => toggleSort("risk_score")}>Score</Th>
                  <Th>Level</Th>
                  <Th>Recommended</Th>
                  <Th sortable active={sortKey === "ts"} desc={sortDesc} onClick={() => toggleSort("ts")}>Time</Th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
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
                    <td className="px-4 py-2 font-mono text-xs text-ink-300">{r.merchant_id}</td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {formatCurrencyShort(r.amount, r.currency)}
                    </td>
                    <td className="px-4 py-2 text-right font-semibold tabular-nums">{r.risk_score}</td>
                    <td className="px-4 py-2"><RiskLevelBadge level={r.risk_level} /></td>
                    <td className="px-4 py-2"><ActionBadge action={r.recommended_action} /></td>
                    <td className="px-4 py-2 text-xs text-ink-400">{formatDateTime(r.ts)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Select({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: readonly string[];
}) {
  return (
    <label className="flex items-center gap-2 text-xs text-ink-400">
      <span className="uppercase tracking-wider">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border-0 bg-ink-800/70 py-1 pl-2 pr-6 text-xs text-ink-100 ring-1 ring-inset ring-ink-600 focus:ring-2 focus:ring-brand-500"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o.replace("_", " ")}</option>
        ))}
      </select>
    </label>
  );
}

function Th({ children, align = "left", sortable, active, desc, onClick }: {
  children: React.ReactNode;
  align?: "left" | "right";
  sortable?: boolean;
  active?: boolean;
  desc?: boolean;
  onClick?: () => void;
}) {
  return (
    <th
      onClick={onClick}
      className={`px-4 py-2 font-medium ${align === "right" ? "text-right" : "text-left"} ${sortable ? "cursor-pointer select-none hover:text-ink-100" : ""} ${active ? "text-ink-200" : ""}`}
    >
      {children}
      {sortable && active && <span className="ml-1 text-ink-400">{desc ? "↓" : "↑"}</span>}
    </th>
  );
}
