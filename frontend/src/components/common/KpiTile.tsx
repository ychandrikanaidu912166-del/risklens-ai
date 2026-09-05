import clsx from "clsx";
import type { ReactNode } from "react";

interface Props {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: "default" | "warn" | "danger" | "good";
}

const ACCENT: Record<NonNullable<Props["accent"]>, string> = {
  default: "text-ink-100",
  warn: "text-risk-high",
  danger: "text-risk-critical",
  good: "text-risk-low",
};

export function KpiTile({ label, value, hint, accent = "default" }: Props) {
  return (
    <div className="card p-4">
      <div className="kpi-label">{label}</div>
      <div className={clsx("kpi-value", ACCENT[accent])}>{value}</div>
      {hint && <div className="mt-1 text-xs text-ink-400">{hint}</div>}
    </div>
  );
}
