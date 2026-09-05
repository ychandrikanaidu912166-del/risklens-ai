import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  AlertTriangle,
  Inbox,
  TrendingUp,
  ArrowUpRight,
  ShieldCheck,
  DollarSign,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { fetchOverviewMetrics } from '../api/client';
import { OverviewMetrics } from '../types';

export const Overview: React.FC = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOverviewMetrics()
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm text-slate-400 font-medium">Loading Risk Operations Intelligence...</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300">
        <h3 className="font-semibold text-base mb-1">Failed to Load Metrics</h3>
        <p className="text-sm">{error || 'Unknown error occurred while contacting the risk API.'}</p>
      </div>
    );
  }

  const chartData = [
    { name: 'Low Risk', count: metrics.risk_distribution.LOW || 0, color: '#10B981' },
    { name: 'Medium', count: metrics.risk_distribution.MEDIUM || 0, color: '#F59E0B' },
    { name: 'High', count: metrics.risk_distribution.HIGH || 0, color: '#F97316' },
    { name: 'Critical', count: metrics.risk_distribution.CRITICAL || 0, color: '#EF4444' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Payment Risk Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time fraud surveillance, multi-signal risk fusion, and live investigation queue.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/investigations')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors shadow-sm shadow-blue-500/20"
          >
            <Inbox className="w-4 h-4" /> Open Investigation Queue
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Transactions */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Ingested</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-white">
            {metrics.total_transactions.toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-400 font-semibold font-mono">100%</span>
            <span>real-time stream scored</span>
          </div>
        </div>

        {/* Review Queue */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Review Queue</span>
            <Inbox className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-amber-400">
            {metrics.review_queue_count}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
            <span>Pending manual review action</span>
          </div>
        </div>

        {/* High & Critical Risk */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">High / Critical Alerts</span>
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-red-400">
            {metrics.high_risk_count + metrics.critical_risk_count}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-2">
            <span className="text-red-400 font-semibold">{metrics.critical_risk_count} Critical</span>
            <span>•</span>
            <span className="text-orange-400 font-semibold">{metrics.high_risk_count} High</span>
          </div>
        </div>

        {/* Expected Business Cost */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Expected Loss Exposure</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold font-mono text-white">
            ₹{metrics.business_cost.toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center gap-1.5">
            <span className="font-mono text-slate-300">₹{metrics.cost_per_tx}/tx</span>
            <span>optimized at optimal threshold</span>
          </div>
        </div>
      </div>

      {/* Held-out ML Performance Row */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-200">
                Held-Out Supervised ML Performance
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 border border-blue-500/20 text-blue-400">
                {metrics.model_version}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly calculated on held-out 20% chronological test set (no future-data leakage).
            </p>
          </div>
          <button
            onClick={() => navigate('/model-monitoring')}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
          >
            Full Model Evaluation <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">Precision</span>
            <div className="text-xl font-mono font-bold text-emerald-400 mt-1">
              {(metrics.precision * 100).toFixed(1)}%
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">Recall</span>
            <div className="text-xl font-mono font-bold text-emerald-400 mt-1">
              {(metrics.recall * 100).toFixed(1)}%
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">F1 Score</span>
            <div className="text-xl font-mono font-bold text-blue-400 mt-1">
              {(metrics.f1 * 100).toFixed(1)}%
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">PR-AUC</span>
            <div className="text-xl font-mono font-bold text-purple-400 mt-1">
              {metrics.pr_auc.toFixed(4)}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">False Pos. Rate</span>
            <div className="text-xl font-mono font-bold text-slate-200 mt-1">
              {(metrics.false_positive_rate * 100).toFixed(2)}%
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">False Neg. Rate</span>
            <div className="text-xl font-mono font-bold text-amber-400 mt-1">
              {(metrics.false_negative_rate * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Middle Section: Risk Distribution Chart & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="lg:col-span-1 p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">Risk Score Distribution</h3>
            <p className="text-xs text-slate-400 mb-4">
              Calibrated breakdown across Low, Medium, High, and Critical thresholds.
            </p>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-800/80 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span className="text-slate-400">Low: {metrics.risk_distribution.LOW || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              <span className="text-slate-400">Medium: {metrics.risk_distribution.MEDIUM || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
              <span className="text-slate-400">High: {metrics.risk_distribution.HIGH || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
              <span className="text-slate-400">Critical: {metrics.risk_distribution.CRITICAL || 0}</span>
            </div>
          </div>
        </div>

        {/* Recent High & Critical Transactions */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Recent High &amp; Critical Investigations</h3>
              <p className="text-xs text-slate-400">Transactions requiring immediate analyst intervention.</p>
            </div>
            <button
              onClick={() => navigate('/investigations')}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              View All Queue →
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="pb-3">Txn ID</th>
                  <th className="pb-3">Customer</th>
                  <th className="pb-3">Amount</th>
                  <th className="pb-3">Score</th>
                  <th className="pb-3">Recommendation</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {metrics.recent_critical_transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 font-mono font-medium text-blue-400">
                      {tx.transaction_id}
                    </td>
                    <td className="py-3 font-mono text-slate-300">{tx.customer_id}</td>
                    <td className="py-3 font-mono font-semibold text-slate-100">
                      ₹{tx.amount.toLocaleString()}
                    </td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded font-bold font-mono text-[11px] ${
                          tx.risk_level === 'CRITICAL'
                            ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                            : 'bg-orange-500/15 text-orange-400 border border-orange-500/30'
                        }`}
                      >
                        {tx.risk_score} {tx.risk_level}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="font-semibold text-slate-300">
                        {tx.policy_recommendation}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => navigate(`/investigations/${tx.transaction_id}`)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors"
                      >
                        Investigate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
