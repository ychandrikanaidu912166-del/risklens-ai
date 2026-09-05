import { useQuery } from "@tanstack/react-query";
import { Sparkles, ShieldCheck } from "lucide-react";
import { api } from "@/api/client";
import { LoadingState, ErrorState } from "@/components/common/States";
import { ConfidenceBadge } from "@/components/common/RiskBadge";

export function AiInvestigation({ txId }: { txId: string }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["ai-report", txId],
    queryFn: () => api.getAIReport(txId),
  });

  if (isLoading) return <LoadingState label="Composing AI investigation…" />;
  if (isError || !data)
    return <ErrorState title="AI investigation unavailable" detail={String(error)} />;

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-brand-500/10 p-1.5 text-brand-500 ring-1 ring-inset ring-brand-500/40">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1 text-sm text-ink-100">{data.assessment}</div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <ConfidenceBadge confidence={data.confidence} />
        <span className="badge bg-ink-800 text-ink-300 ring-ink-600">
          {data.generated_by === "llm" ? "LLM-composed" : "Deterministic template"}
        </span>
        <span className="badge bg-risk-low/10 text-risk-low ring-risk-low/30">
          <ShieldCheck className="h-3 w-3" />
          {data.grounded ? "Grounded" : "Ungrounded"}
        </span>
      </div>

      <div>
        <div className="section-title mb-1.5">Primary reasons</div>
        <ul className="space-y-1 text-sm text-ink-200">
          {data.primary_reasons.map((r, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-ink-400" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>

      {data.counter_evidence_ids.length > 0 && (
        <div>
          <div className="section-title mb-1.5">Counter-signals considered</div>
          <div className="flex flex-wrap gap-1">
            {data.counter_evidence_ids.map((id) => (
              <code key={id} className="rounded bg-ink-800/70 px-1.5 py-0.5 text-2xs text-ink-300">{id}</code>
            ))}
          </div>
        </div>
      )}

      {data.entity_notes.length > 0 && (
        <div>
          <div className="section-title mb-1.5">Entity notes</div>
          <ul className="space-y-1 text-xs text-ink-300">
            {data.entity_notes.map((n, i) => (<li key={i}>• {n}</li>))}
          </ul>
        </div>
      )}

      <div>
        <div className="section-title mb-1.5">Analyst summary</div>
        <p className="text-sm text-ink-200">{data.analyst_summary}</p>
      </div>

      <div className="rounded-md border border-ink-700/60 bg-ink-800/40 p-3 text-2xs text-ink-400">
        {data.disclaimer}
      </div>
    </div>
  );
}
