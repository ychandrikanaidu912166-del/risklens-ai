import clsx from "clsx";
import { Minus, Plus } from "lucide-react";
import type { Evidence } from "@/api/types";

const SOURCE_LABEL: Record<string, string> = {
  rule: "Rule",
  model: "ML Model",
  behavior: "Behaviour",
  velocity: "Velocity",
  anomaly: "Anomaly",
  entity: "Entity",
};

function EvidenceRow({ e, positive }: { e: Evidence; positive: boolean }) {
  const bar = Math.min(60, Math.abs(e.weight) * 1.8);
  return (
    <div className="rounded-md border border-ink-700/60 bg-ink-900/60 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <code className="rounded bg-ink-800/80 px-1.5 py-0.5 text-2xs text-ink-300">{e.id}</code>
            <span className="text-2xs uppercase tracking-wider text-ink-400">
              {SOURCE_LABEL[e.source] ?? e.source}
            </span>
          </div>
          <div className="mt-1.5 text-sm text-ink-100">{e.description}</div>
        </div>
        <div
          className={clsx(
            "flex shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset",
            positive
              ? "bg-risk-critical/10 text-risk-critical ring-risk-critical/30"
              : "bg-risk-low/10 text-risk-low ring-risk-low/30",
          )}
        >
          {positive ? <Plus className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
          <span className="tabular-nums">{Math.abs(e.weight).toFixed(1)}</span>
        </div>
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-ink-800/60">
        <div
          className={clsx("h-full", positive ? "bg-risk-critical/70" : "bg-risk-low/70")}
          style={{ width: `${bar}%` }}
        />
      </div>
    </div>
  );
}

export function EvidenceList({ items, kind }: { items: Evidence[]; kind: "positive" | "counter" }) {
  const positive = kind === "positive";
  if (items.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-ink-700/60 p-4 text-center text-xs text-ink-400">
        {positive ? "No positive-risk evidence." : "No counter-evidence."}
      </div>
    );
  }
  const sorted = [...items].sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight));
  return (
    <div className="space-y-2">
      {sorted.map((e) => (
        <EvidenceRow key={e.id} e={e} positive={positive} />
      ))}
    </div>
  );
}
