import type { ModelExplanation } from "@/api/types";

export function ShapWaterfall({ explanation }: { explanation: ModelExplanation }) {
  const items = explanation.top_features.slice(0, 8);
  const maxAbs = items.reduce((m, x) => Math.max(m, Math.abs(x.contribution)), 0.0001);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-2xs uppercase tracking-wider text-ink-400">
        <span>Feature</span>
        <span>Contribution ({explanation.method})</span>
      </div>
      <div className="space-y-1.5">
        {items.map((f) => {
          const pct = (Math.abs(f.contribution) / maxAbs) * 100;
          const positive = f.contribution >= 0;
          return (
            <div key={f.feature} className="text-sm">
              <div className="flex items-center justify-between text-xs text-ink-300">
                <div className="min-w-0 truncate font-mono">
                  {f.feature} <span className="text-ink-500">= {typeof f.value === "number" ? Number(f.value).toFixed(2) : String(f.value)}</span>
                </div>
                <div
                  className={
                    positive
                      ? "font-semibold tabular-nums text-risk-critical"
                      : "font-semibold tabular-nums text-risk-low"
                  }
                >
                  {positive ? "+" : ""}
                  {f.contribution.toFixed(3)}
                </div>
              </div>
              <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-ink-800/60">
                <div className="flex-1 border-r border-ink-800 bg-transparent">
                  {!positive && (
                    <div
                      className="ml-auto h-full bg-risk-low/70"
                      style={{ width: `${pct}%` }}
                    />
                  )}
                </div>
                <div className="flex-1">
                  {positive && (
                    <div className="h-full bg-risk-critical/70" style={{ width: `${pct}%` }} />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
