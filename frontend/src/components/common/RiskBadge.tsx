import clsx from "clsx";
import type { Action, RiskLevel } from "@/api/types";

const RISK_STYLE: Record<RiskLevel, string> = {
  LOW: "bg-risk-low/10 text-risk-low ring-risk-low/40",
  MEDIUM: "bg-risk-medium/10 text-risk-medium ring-risk-medium/40",
  HIGH: "bg-risk-high/10 text-risk-high ring-risk-high/40",
  CRITICAL: "bg-risk-critical/15 text-risk-critical ring-risk-critical/40",
};

const ACTION_STYLE: Record<Action, string> = {
  APPROVE: "bg-risk-low/10 text-risk-low ring-risk-low/40",
  STEP_UP: "bg-risk-medium/10 text-risk-medium ring-risk-medium/40",
  MANUAL_REVIEW: "bg-brand-500/10 text-brand-500 ring-brand-500/40",
  HOLD: "bg-risk-high/10 text-risk-high ring-risk-high/40",
  BLOCK: "bg-risk-critical/15 text-risk-critical ring-risk-critical/40",
};

export function RiskLevelBadge({ level, className }: { level: RiskLevel; className?: string }) {
  return <span className={clsx("badge", RISK_STYLE[level], className)}>{level}</span>;
}

export function ActionBadge({ action, className }: { action: Action; className?: string }) {
  return (
    <span className={clsx("badge", ACTION_STYLE[action], className)}>
      {action.replace("_", " ")}
    </span>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: string }) {
  const styleMap: Record<string, string> = {
    low: "bg-ink-800 text-ink-300 ring-ink-600",
    medium: "bg-brand-500/10 text-brand-500 ring-brand-500/40",
    high: "bg-risk-low/10 text-risk-low ring-risk-low/40",
  };
  return (
    <span className={clsx("badge", styleMap[confidence] || styleMap.low)}>
      {confidence.toUpperCase()} CONFIDENCE
    </span>
  );
}
