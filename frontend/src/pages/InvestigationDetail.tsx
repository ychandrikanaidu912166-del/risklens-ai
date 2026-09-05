import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Smartphone,
  Globe,
  User,
  Activity,
  Sparkles,
  CheckCircle,
  XCircle,
  PauseCircle,
  Flag,
  RotateCcw,
  Layers,
  Info,
} from 'lucide-react';
import {
  fetchInvestigationDetail,
  triggerAIAnalysis,
  submitAnalystDecision,
} from '../api/client';
import { InvestigationContext, AIAssessment } from '../types';
import { RiskScoreGauge } from '../components/RiskScoreGauge';
import { EntityGraphView } from '../components/EntityGraphView';

export const InvestigationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [context, setContext] = useState<InvestigationContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI re-analysis state
  const [analyzing, setAnalyzing] = useState(false);

  // Analyst form state
  const [selectedDecision, setSelectedDecision] = useState<string>('HOLD');
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const loadData = () => {
    if (!id) return;
    setLoading(true);
    fetchInvestigationDetail(id)
      .then((data) => {
        setContext(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleTriggerAI = async () => {
    if (!id) return;
    setAnalyzing(true);
    try {
      const assessment = await triggerAIAnalysis(id);
      if (context) {
        setContext({ ...context, ai_investigation: assessment });
      }
    } catch (err: any) {
      alert(`AI Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !decisionReason.trim()) return;

    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      await submitAnalystDecision(id, {
        decision: selectedDecision,
        reason: decisionReason.trim(),
        analyst_id: 'senior_analyst_ops',
      });
      setSubmitSuccess(`Decision '${selectedDecision}' submitted and recorded in audit log.`);
      setDecisionReason('');
      // Reload updated context to show resolution status and timeline
      loadData();
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to submit decision.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm text-slate-400">Loading Investigation Context for {id}...</p>
      </div>
    );
  }

  if (error || !context) {
    return (
      <div className="max-w-4xl mx-auto p-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300">
        <h3 className="font-semibold text-base mb-1">Failed to Load Investigation</h3>
        <p className="text-sm">{error || 'Investigation context not found.'}</p>
        <button
          onClick={() => navigate('/investigations')}
          className="mt-4 inline-flex items-center gap-1 text-xs text-blue-400 hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Queue
        </button>
      </div>
    );
  }

  const { transaction, customer_behaviour } = context;
  const ai = context.ai_investigation;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Navigation & Header */}
      <div className="flex flex-col gap-3">
        <button
          onClick={() => navigate('/investigations')}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Queue
        </button>

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <ShieldAlert className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-xl font-bold font-mono text-white tracking-tight">
                  {transaction.transaction_id}
                </h1>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase bg-slate-800 border border-slate-700 text-slate-300">
                  {transaction.payment_method.toUpperCase()}
                </span>
                {context.existing_decision && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> Resolved ({context.existing_decision.decision})
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-400 font-mono">
                <span>Customer: <strong className="text-slate-200">{transaction.customer_id}</strong></span>
                <span>•</span>
                <span>Merchant: <strong className="text-slate-200">{transaction.merchant_id}</strong></span>
                <span>•</span>
                <span>Amount: <strong className="text-white text-sm font-sans">₹{transaction.amount.toLocaleString()}</strong></span>
                <span>•</span>
                <span>Time: {new Date(transaction.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Quick Decision / Recommendation pill */}
          <div className="flex items-center gap-6 self-end lg:self-center">
            <div className="text-right">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Policy Recommendation
              </span>
              <span className="text-base font-extrabold text-blue-400">
                {context.recommended_action}
              </span>
            </div>
            <RiskScoreGauge score={context.risk_score} level={context.risk_level} size={100} />
          </div>
        </div>
      </div>

      {/* Grid: 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Evidence, Behaviour, Entities, Timeline */}
        <div className="lg:col-span-2 space-y-8">
          {/* SECTION 1: WHY IS THIS TRANSACTION RISKY? */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  Why is this Transaction Risky?
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Explainable mathematical decomposition of individual factor point contributions.
                </p>
              </div>
              <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {context.risk_factors.length} Active Signals
              </span>
            </div>

            <div className="space-y-2.5">
              {context.risk_factors.map((factor, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between gap-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-200">{factor.name}</span>
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {factor.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{factor.detail}</p>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`text-sm font-bold font-mono ${
                        factor.contribution > 0 ? 'text-red-400' : 'text-emerald-400'
                      }`}
                    >
                      {factor.contribution > 0 ? `+${factor.contribution}` : factor.contribution} pts
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 2: CUSTOMER BEHAVIOUR BASELINE COMPARISON */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <User className="w-5 h-5 text-emerald-400" />
                Customer Behaviour Baseline
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Current transaction parameters directly contrasted against customer's empirical profile.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Amount Comparison */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold uppercase">Amount Ratio</span>
                <div className="mt-2 flex items-baseline justify-between">
                  <div className="text-xl font-mono font-bold text-white">
                    ₹{transaction.amount.toLocaleString()}
                  </div>
                  <div
                    className={`text-sm font-bold font-mono px-2 py-0.5 rounded ${
                      customer_behaviour.amount_comparison.is_anomaly
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {customer_behaviour.amount_comparison.amount_ratio}x avg
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Customer historical average: ₹{customer_behaviour.amount_comparison.baseline_avg.toLocaleString()} (Median: ₹{customer_behaviour.amount_comparison.baseline_median.toLocaleString()})
                </p>
              </div>

              {/* Hardware Device */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold uppercase">Hardware Fingerprint</span>
                <div className="mt-2 flex items-baseline justify-between">
                  <div className="text-xs font-mono font-bold text-slate-200 truncate max-w-[180px]">
                    {transaction.device_id || 'Unknown'}
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                      customer_behaviour.device_comparison.is_new_device
                        ? 'bg-amber-500/15 border-amber-500/30 text-amber-300'
                        : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                    }`}
                  >
                    {customer_behaviour.device_comparison.is_new_device ? 'New Device' : 'Verified Device'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-2 truncate">
                  Registered: {customer_behaviour.device_comparison.known_devices.join(', ') || 'None previously on file'}
                </p>
              </div>

              {/* Geolocation */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold uppercase">Country / Jurisdiction</span>
                <div className="mt-2 flex items-baseline justify-between">
                  <div className="text-base font-mono font-bold text-white">
                    {transaction.country}
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                      customer_behaviour.country_comparison.is_new_country
                        ? 'bg-red-500/15 border-red-500/30 text-red-400'
                        : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                    }`}
                  >
                    {customer_behaviour.country_comparison.is_new_country ? 'Foreign / New' : 'Domestic Match'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Usual Countries: {customer_behaviour.country_comparison.known_countries.join(', ')}
                </p>
              </div>

              {/* Velocity */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 font-semibold uppercase">Velocity Burden</span>
                <div className="mt-2 flex items-baseline justify-between">
                  <div className="text-base font-mono font-bold text-white">
                    {transaction.transactions_last_10m} txns in 10m
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                      customer_behaviour.velocity_comparison.is_anomaly
                        ? 'bg-red-500/15 border-red-500/30 text-red-400'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {customer_behaviour.velocity_comparison.is_anomaly ? 'Velocity Burst' : 'Calm'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  1 hour: {transaction.transactions_last_1h} | 24 hour: {transaction.transactions_last_24h}
                </p>
              </div>
            </div>
          </div>

          {/* SECTION 3: EVIDENCE CHAIN & COUNTER-EVIDENCE */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-400" />
                Structured Evidence &amp; Counter-Evidence
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Balancing incriminating risk signals against legitimate trust markers.
              </p>
            </div>

            {/* Incriminating Evidence */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-red-400 mb-3 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Detected Risk Evidence ({context.evidence.length})
              </h4>
              <div className="space-y-2">
                {context.evidence.map((ev) => (
                  <div
                    key={ev.evidence_id}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-semibold text-slate-200">
                        [{ev.type}] {ev.source}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                          ev.severity === 'CRITICAL'
                            ? 'bg-red-500/15 border-red-500/30 text-red-400'
                            : ev.severity === 'HIGH'
                            ? 'bg-orange-500/15 border-orange-500/30 text-orange-400'
                            : 'bg-amber-500/15 border-amber-500/30 text-amber-300'
                        }`}
                      >
                        {ev.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-2">{ev.description}</p>
                    {ev.observed_value && (
                      <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-4">
                        <span>Observed: <strong className="text-slate-200">{ev.observed_value}</strong></span>
                        <span>Baseline: <strong className="text-slate-400">{ev.baseline_value}</strong></span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Counter-Evidence */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-3 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" /> Legitimate Counter-Evidence ({context.counter_evidence.length})
              </h4>
              <div className="space-y-2">
                {context.counter_evidence.map((cev) => (
                  <div
                    key={cev.id}
                    className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-emerald-300">{cev.title}</span>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        {cev.confidence_impact} pts
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{cev.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION 4: ENTITY GRAPH */}
          <EntityGraphView graph={context.entities} />

          {/* SECTION 5: TIMELINE */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-1">
              <Clock className="w-5 h-5 text-cyan-400" />
              Investigation Timeline
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Chronological order of authenticated sessions, payment attempts, and risk evaluations.
            </p>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {context.timeline.map((event) => (
                <div key={event.id} className="relative">
                  <span
                    className={`absolute -left-6 top-1 w-2.5 h-2.5 rounded-full ring-4 ring-slate-950 ${
                      event.severity === 'CRITICAL'
                        ? 'bg-red-500'
                        : event.severity === 'WARNING'
                        ? 'bg-orange-400'
                        : 'bg-blue-400'
                    }`}
                  ></span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-200">{event.title}</span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{event.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): AI Investigator & Analyst Decision Workbench */}
        <div className="space-y-8">
          {/* SECTION 6: AI INVESTIGATOR */}
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white">AI Investigator</h3>
              </div>
              <button
                onClick={handleTriggerAI}
                disabled={analyzing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/30 text-xs font-semibold transition-colors disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
                {analyzing ? 'Analyzing...' : 'Re-Analyze'}
              </button>
            </div>

            {/* Provider Badge */}
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
              <span className="text-slate-400">Synthesis Engine:</span>
              <span className="font-mono text-purple-400 font-semibold">
                {ai?.provider || 'local_deterministic_engine'}
              </span>
            </div>

            {ai && (
              <div className="space-y-4 text-xs">
                {/* Assessment */}
                <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20">
                  <span className="font-semibold text-purple-300 block mb-1">
                    Synthesized Assessment
                  </span>
                  <p className="text-slate-200 leading-relaxed">{ai.assessment}</p>
                  <div className="mt-2 text-[11px] text-purple-400 font-mono font-semibold">
                    Confidence: {(ai.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                {/* Primary Evidence */}
                <div>
                  <span className="font-semibold text-slate-300 block mb-1.5">
                    Primary Evidence Drivers
                  </span>
                  <ul className="space-y-1">
                    {ai.primary_evidence.map((p, i) => (
                      <li key={i} className="text-slate-400 flex items-start gap-1.5">
                        <span className="text-red-400">•</span> {p}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Counter Evidence in AI */}
                {ai.counter_evidence.length > 0 && (
                  <div>
                    <span className="font-semibold text-slate-300 block mb-1.5">
                      Counter-Evidence Noted
                    </span>
                    <ul className="space-y-1">
                      {ai.counter_evidence.map((c, i) => (
                        <li key={i} className="text-slate-400 flex items-start gap-1.5">
                          <span className="text-emerald-400">•</span> {c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Reasoning summary */}
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="font-semibold text-slate-400 block mb-1">Reasoning Summary</span>
                  <p className="text-slate-300 leading-relaxed">{ai.reasoning_summary}</p>
                </div>
              </div>
            )}
          </div>

          {/* SECTION 7: ANALYST DECISION WORKBENCH */}
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                Analyst Decision Workbench
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Human-in-the-loop override. All actions are immutably signed to the audit log.
              </p>
            </div>

            {submitSuccess && (
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                {submitSuccess}
              </div>
            )}

            {submitError && (
              <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
                {submitError}
              </div>
            )}

            <form onSubmit={handleSubmitDecision} className="space-y-4">
              {/* Decision Action Selector */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-2">
                  Select Action
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'APPROVE', label: 'Approve', color: 'hover:border-emerald-500 hover:text-emerald-400' },
                    { key: 'HOLD', label: 'Hold', color: 'hover:border-amber-500 hover:text-amber-400' },
                    { key: 'BLOCK', label: 'Block', color: 'hover:border-red-500 hover:text-red-400' },
                    { key: 'FALSE_POSITIVE', label: 'False Positive', color: 'hover:border-purple-500 hover:text-purple-400' },
                  ].map((act) => (
                    <button
                      key={act.key}
                      type="button"
                      onClick={() => setSelectedDecision(act.key)}
                      className={`p-2.5 rounded-lg border text-xs font-semibold transition-all ${
                        selectedDecision === act.key
                          ? 'bg-blue-600 border-blue-500 text-white shadow-sm shadow-blue-500/20'
                          : `bg-slate-950/80 border-slate-800 text-slate-300 ${act.color}`
                      }`}
                    >
                      {act.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reason Input */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Analyst Rationale / Evidence Note <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="Explain why this decision was chosen (e.g. Verified customer confirmed travel via phone OTP)..."
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  className="w-full p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={submitting || !decisionReason.trim()}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold text-xs transition-colors shadow-sm shadow-blue-500/20"
              >
                {submitting ? 'Recording Audit Signature...' : `Submit Decision (${selectedDecision})`}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
