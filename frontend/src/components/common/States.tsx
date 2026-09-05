import { AlertTriangle, Loader2, Inbox } from "lucide-react";
import type { ReactNode } from "react";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-sm text-ink-300">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ title, detail, action }: { title: string; detail?: ReactNode; action?: ReactNode }) {
  return (
    <div className="card p-6">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-md bg-risk-critical/10 p-1.5 text-risk-critical ring-1 ring-inset ring-risk-critical/30">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-ink-100">{title}</div>
          {detail && <div className="mt-1 text-xs text-ink-300">{detail}</div>}
          {action && <div className="mt-3">{action}</div>}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center justify-center gap-2 py-10 text-center">
      <Inbox className="h-6 w-6 text-ink-400" />
      <div className="text-sm font-medium text-ink-200">{title}</div>
      {detail && <div className="max-w-md text-xs text-ink-400">{detail}</div>}
    </div>
  );
}
