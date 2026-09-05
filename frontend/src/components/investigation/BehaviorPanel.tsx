import { AlertCircle, Check } from "lucide-react";
import type { BehaviorSnapshot, InvestigationResult } from "@/api/types";
import { formatAmount, formatNumber } from "@/components/common/format";

export function BehaviorPanel({ inv }: { inv: InvestigationResult }) {
  const b = inv.behavior;
  const rows = buildRows(inv, b);
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div
          key={r.label}
          className="flex items-start gap-3 rounded-md border border-ink-700/60 bg-ink-900/60 p-3"
        >
          <div
            className={
              r.flagged
                ? "mt-0.5 rounded-md bg-risk-high/10 p-1 text-risk-high ring-1 ring-inset ring-risk-high/30"
                : "mt-0.5 rounded-md bg-risk-low/10 p-1 text-risk-low ring-1 ring-inset ring-risk-low/30"
            }
          >
            {r.flagged ? <AlertCircle className="h-4 w-4" /> : <Check className="h-4 w-4" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs uppercase tracking-wider text-ink-400">{r.label}</div>
            <div className="mt-0.5 text-sm text-ink-100">{r.now}</div>
            <div className="mt-0.5 text-xs text-ink-400">Baseline: {r.baseline}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

interface Row {
  label: string;
  now: string;
  baseline: string;
  flagged: boolean;
}

function buildRows(inv: InvestigationResult, b: BehaviorSnapshot): Row[] {
  const amountFlagged = b.amount_z_score !== null && Math.abs(b.amount_z_score) >= 1.5;
  const amountBaseline =
    b.mean_amount !== null
      ? `${formatAmount(b.mean_amount, inv.currency)} avg over ${formatNumber(b.n_prior_tx)} prior tx`
      : "no prior history";

  const countries = b.common_countries.length
    ? b.common_countries.join(", ")
    : "no baseline yet";
  const devices = b.known_devices.length ? `${b.known_devices.length} known device(s)` : "no known devices";

  const hoursBaseline = b.common_hours.length
    ? `Usual hours: ${b.common_hours
        .slice()
        .sort((a, x) => a - x)
        .map((h) => String(h).padStart(2, "0"))
        .join(", ")}`
    : "no baseline yet";

  return [
    {
      label: "Amount",
      now: formatAmount(inv.amount, inv.currency)
        + (b.amount_z_score !== null ? ` (${b.amount_z_score.toFixed(1)}σ from baseline)` : ""),
      baseline: amountBaseline,
      flagged: amountFlagged,
    },
    {
      label: "Device",
      now: inv.entities.find((e) => e.type === "device")?.id ?? "unknown",
      baseline: devices,
      flagged: b.is_new_device,
    },
    {
      label: "Location (IP country)",
      now: `${(inv.entities.find((e) => e.type === "ip")?.id ?? "").slice(0, 12)}…`
        + " · vs customer",
      baseline: countries,
      flagged: b.is_new_country,
    },
    {
      label: "Transaction hour",
      now: `${String(new Date(inv.ts).getUTCHours()).padStart(2, "0")}:00 UTC`,
      baseline: hoursBaseline,
      flagged: b.unusual_hour,
    },
    {
      label: "Prior transaction count",
      now: `${b.n_prior_tx} priors`,
      baseline: b.n_prior_tx < 5 ? "very thin history — treat cautiously" : "sufficient history",
      flagged: b.n_prior_tx < 5,
    },
  ];
}
