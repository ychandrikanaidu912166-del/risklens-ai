import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PauseCircle, Ban, XCircle, ArrowUpRight } from "lucide-react";
import { api } from "@/api/client";
import type { AnalystAction, Decision } from "@/api/types";
import { formatDateTime, relativeTime } from "@/components/common/format";

const CHOICES: { action: AnalystAction; label: string; className: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { action: "APPROVE", label: "Approve", className: "btn-success", icon: CheckCircle2 },
  { action: "HOLD", label: "Hold", className: "btn-warning", icon: PauseCircle },
  { action: "BLOCK", label: "Block", className: "btn-danger", icon: Ban },
  { action: "FALSE_POSITIVE", label: "False positive", className: "btn-ghost", icon: XCircle },
  { action: "ESCALATE", label: "Escalate", className: "btn-primary", icon: ArrowUpRight },
];

export function DecisionPanel({ txId }: { txId: string }) {
  const [selected, setSelected] = useState<AnalystAction | null>(null);
  const [reason, setReason] = useState("");
  const qc = useQueryClient();

  const decisions = useQuery({
    queryKey: ["decisions", txId],
    queryFn: () => api.listDecisions(txId),
  });

  const submit = useMutation({
    mutationFn: () =>
      api.postDecision({
        tx_id: txId,
        action: selected!,
        reason: reason.trim() || undefined,
        analyst_id: "demo",
      }),
    onSuccess: () => {
      setReason("");
      setSelected(null);
      qc.invalidateQueries({ queryKey: ["decisions", txId] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  return (
    <div className="space-y-4">
      <div>
        <div className="section-title mb-2">Analyst decision</div>
        <div className="grid grid-cols-2 gap-2 xl:grid-cols-5">
          {CHOICES.map(({ action, label, className, icon: Icon }) => (
            <button
              key={action}
              type="button"
              onClick={() => setSelected(action)}
              className={`btn ${className} ${selected === action ? "ring-2" : ""}`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs uppercase tracking-wider text-ink-400">Reason (optional)</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          placeholder="Add analyst notes for the audit trail…"
          className="input font-normal"
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="text-2xs text-ink-400">
          Feedback is stored as controlled evaluation data — it does NOT retrain the model automatically.
        </div>
        <button
          type="button"
          disabled={!selected || submit.isPending}
          onClick={() => submit.mutate()}
          className="btn btn-primary"
        >
          {submit.isPending ? "Submitting…" : "Record decision"}
        </button>
      </div>

      {submit.isSuccess && (
        <div className="rounded-md border border-risk-low/40 bg-risk-low/10 p-2 text-xs text-risk-low">
          Decision recorded and written to the audit trail.
        </div>
      )}
      {submit.isError && (
        <div className="rounded-md border border-risk-critical/40 bg-risk-critical/10 p-2 text-xs text-risk-critical">
          Failed to record decision: {String(submit.error)}
        </div>
      )}

      <div>
        <div className="section-title mb-2">Decision history</div>
        {decisions.isLoading ? (
          <div className="text-xs text-ink-400">Loading…</div>
        ) : !decisions.data || decisions.data.length === 0 ? (
          <div className="text-xs text-ink-400">No decisions yet for this transaction.</div>
        ) : (
          <ul className="space-y-1.5">
            {decisions.data.map((d: Decision) => (
              <li key={d.id} className="rounded-md border border-ink-700/60 bg-ink-900/60 p-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-ink-100">{d.action.replace("_", " ")}</span>
                  <span className="text-ink-400" title={formatDateTime(d.created_at)}>{relativeTime(d.created_at)}</span>
                </div>
                <div className="mt-0.5 text-ink-300">
                  by <span className="font-mono">{d.analyst_id}</span>
                  {d.reason && <> — {d.reason}</>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
