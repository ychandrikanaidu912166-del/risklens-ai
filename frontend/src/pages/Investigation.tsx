import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { api } from "@/api/client";
import { LoadingState, ErrorState } from "@/components/common/States";
import { ScoreDial } from "@/components/common/ScoreDial";
import { ActionBadge, RiskLevelBadge } from "@/components/common/RiskBadge";
import { EvidenceList } from "@/components/investigation/EvidenceList";
import { ShapWaterfall } from "@/components/investigation/ShapWaterfall";
import { BehaviorPanel } from "@/components/investigation/BehaviorPanel";
import { Timeline } from "@/components/investigation/Timeline";
import { EntityGraph } from "@/components/investigation/EntityGraph";
import { AiInvestigation } from "@/components/investigation/AiInvestigation";
import { DecisionPanel } from "@/components/investigation/DecisionPanel";
import { formatAmount, formatDateTime, formatPercent } from "@/components/common/format";

export function Investigation() {
  const { txId = "" } = useParams();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["investigation", txId],
    queryFn: () => api.getInvestigation(txId),
    enabled: !!txId,
  });

  if (isLoading) return <LoadingState label="Loading investigation…" />;
  if (isError || !data)
    return (
      <ErrorState
        title={`Could not load investigation ${txId}`}
        detail={String(error)}
        action={
          <Link to="/investigations" className="btn btn-ghost">
            <ArrowLeft className="h-4 w-4" /> Back to queue
          </Link>
        }
      />
    );

  return (
    <div className="space-y-6">
      <div>
        <Link to="/investigations" className="inline-flex items-center gap-1 text-xs text-ink-400 hover:text-ink-200">
          <ArrowLeft className="h-3 w-3" /> Investigation queue
        </Link>
        <div className="mt-1 flex items-center gap-3">
          <h1 className="font-mono text-lg font-semibold text-ink-100">{data.transaction_id}</h1>
          <RiskLevelBadge level={data.risk_level} />
          <ActionBadge action={data.recommended_action} />
        </div>
        <div className="mt-1 text-xs text-ink-400">
          Amount: <span className="tabular-nums text-ink-200">{formatAmount(data.amount, data.currency)}</span>
          {" · "}Customer: <span className="font-mono text-ink-200">{data.customer_id}</span>
          {" · "}Merchant: <span className="font-mono text-ink-200">{data.merchant_id}</span>
          {" · "}Scored at <span className="tabular-nums">{formatDateTime(data.created_at)}</span>
        </div>
      </div>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Risk summary */}
        <div className="card p-4 xl:col-span-1">
          <div className="flex items-center gap-6">
            <ScoreDial score={data.risk_score} level={data.risk_level} />
            <div className="space-y-2">
              <div>
                <div className="section-title">Model probability</div>
                <div className="text-lg font-semibold tabular-nums text-ink-100">
                  {formatPercent(data.fraud_probability, 2)}
                </div>
              </div>
              <div>
                <div className="section-title">Behavioural deviation</div>
                <div className="text-lg font-semibold tabular-nums text-ink-100">
                  {data.behavioral_deviation.toFixed(1)}
                </div>
              </div>
              <div>
                <div className="section-title">Anomaly score</div>
                <div className="text-lg font-semibold tabular-nums text-ink-100">
                  {data.anomaly_score.toFixed(3)}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 rounded-md border border-ink-700/60 bg-ink-800/40 p-3 text-xs text-ink-300">
            {data.explanation}
          </div>
        </div>

        {/* AI investigation */}
        <div className="card p-4 xl:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="card-title">AI Investigation</div>
              <div className="card-subtitle">Grounded summary — does not classify fraud on its own.</div>
            </div>
          </div>
          <AiInvestigation txId={txId} />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="card p-4">
          <div className="mb-3">
            <div className="card-title">Why is this risky?</div>
            <div className="card-subtitle">Evidence contributing risk points.</div>
          </div>
          <EvidenceList items={data.supporting_evidence} kind="positive" />
        </div>
        <div className="card p-4">
          <div className="mb-3">
            <div className="card-title">Why might this be legitimate?</div>
            <div className="card-subtitle">Counter-evidence considered by the engine.</div>
          </div>
          <EvidenceList items={data.counter_evidence} kind="counter" />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="card p-4 xl:col-span-1">
          <div className="mb-3">
            <div className="card-title">Customer behaviour</div>
            <div className="card-subtitle">Current vs baseline.</div>
          </div>
          <BehaviorPanel inv={data} />
        </div>
        <div className="card p-4 xl:col-span-1">
          <div className="mb-3">
            <div className="card-title">Model explanation</div>
            <div className="card-subtitle">Top feature contributions ({data.model_explanation.method}).</div>
          </div>
          <ShapWaterfall explanation={data.model_explanation} />
        </div>
        <div className="card p-4 xl:col-span-1">
          <div className="mb-3">
            <div className="card-title">Timeline</div>
            <div className="card-subtitle">Chronological events.</div>
          </div>
          <Timeline events={data.timeline} />
        </div>
      </section>

      <section className="card p-4">
        <div className="mb-3">
          <div className="card-title">Connected entities</div>
          <div className="card-subtitle">Ego-graph around this customer.</div>
        </div>
        <EntityGraph rootType="customer" rootId={data.customer_id} />
      </section>

      <section className="card p-4">
        <div className="mb-3">
          <div className="card-title">Analyst decision</div>
          <div className="card-subtitle">Record your assessment — feedback stored, model NOT auto-retrained.</div>
        </div>
        <DecisionPanel txId={data.transaction_id} />
      </section>
    </div>
  );
}
