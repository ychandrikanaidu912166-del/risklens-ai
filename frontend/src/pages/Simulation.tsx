import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Zap,
  RotateCcw,
  Sliders,
  DollarSign,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import { fetchSimulationPresets, simulateTransaction } from '../api/client';
import { SimulationPreset, SimulationResult } from '../types';
import { RiskScoreGauge } from '../components/RiskScoreGauge';

export const Simulation: React.FC = () => {
  const navigate = useNavigate();
  const [presets, setPresets] = useState<SimulationPreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('preset_ato');
  const [loadingPresets, setLoadingPresets] = useState<boolean>(true);

  // Editable transaction form fields
  const [amount, setAmount] = useState<number>(48500);
  const [customerId, setCustomerId] = useState<string>('cust_sim_ato_victim');
  const [merchantId, setMerchantId] = useState<string>('merch_002');
  const [deviceId, setDeviceId] = useState<string>('dev_hacker_proxy_99');
  const [ipAddress, setIpAddress] = useState<string>('185.220.101.45');
  const [country, setCountry] = useState<string>('IN');
  const [paymentMethod, setPaymentMethod] = useState<string>('credit_card');
  const [velocity10m, setVelocity10m] = useState<number>(4);
  const [velocity1h, setVelocity1h] = useState<number>(7);
  const [isNewDevice, setIsNewDevice] = useState<number>(1);
  const [isNewCountry, setIsNewCountry] = useState<number>(0);

  // Simulation execution state
  const [running, setRunning] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSimulationPresets()
      .then((data) => {
        setPresets(data);
        setLoadingPresets(false);
        if (data.length > 0) {
          applyPreset(data[0]);
        }
      })
      .catch((err) => {
        setError(err.message);
        setLoadingPresets(false);
      });
  }, []);

  const applyPreset = (preset: SimulationPreset) => {
    setSelectedPresetId(preset.id);
    const p = preset.payload;
    if (p.amount !== undefined) setAmount(p.amount);
    if (p.customer_id) setCustomerId(p.customer_id);
    if (p.merchant_id) setMerchantId(p.merchant_id);
    if (p.device_id) setDeviceId(p.device_id);
    if (p.ip_address) setIpAddress(p.ip_address);
    if (p.country) setCountry(p.country);
    if (p.payment_method) setPaymentMethod(p.payment_method);
    if (p.transactions_last_10m !== undefined) setVelocity10m(p.transactions_last_10m);
    if (p.transactions_last_1h !== undefined) setVelocity1h(p.transactions_last_1h);
    if (p.is_new_device !== undefined) setIsNewDevice(p.is_new_device);
    if (p.is_new_country !== undefined) setIsNewCountry(p.is_new_country);
  };

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setError(null);
    setSimulationResult(null);

    const payload = {
      amount: Number(amount),
      currency: 'INR',
      customer_id: customerId,
      merchant_id: merchantId,
      device_id: deviceId,
      ip_address: ipAddress,
      country: country,
      payment_method: paymentMethod,
      transactions_last_10m: Number(velocity10m),
      transactions_last_1h: Number(velocity1h),
      transactions_last_24h: Number(velocity1h) + 2,
      is_new_device: Number(isNewDevice),
      is_new_country: Number(isNewCountry),
      customer_avg_amount: amount > 20000 ? 3500.0 : 1500.0,
      customer_transaction_count: 18,
    };

    try {
      const res = await simulateTransaction(payload);
      setSimulationResult(res);
    } catch (err: any) {
      setError(err.message || 'Simulation execution failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Real-Time Payment Risk Simulator
          </h1>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-500/15 border border-blue-500/30 text-blue-400">
            Live Pipeline Execution
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Execute real-time transactions through the actual feature extraction, supervised ML, behavioral baselining, and policy decision engines.
        </p>
      </div>

      {/* Preset Selector Banner */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" /> Select Scenario Preset
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {presets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => applyPreset(preset)}
              className={`p-3 rounded-xl border text-left transition-all ${
                selectedPresetId === preset.id
                  ? 'bg-blue-600/15 border-blue-500 text-white shadow-sm shadow-blue-500/20 ring-1 ring-blue-500'
                  : 'bg-slate-950/70 border-slate-800/90 text-slate-300 hover:border-slate-700'
              }`}
            >
              <span className="text-[10px] font-mono font-semibold uppercase block text-blue-400 mb-1">
                {preset.category}
              </span>
              <span className="text-xs font-bold block truncate">{preset.name}</span>
              <span className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                {preset.description}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Inputs on Left, Real Pipeline Trace on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Transaction Configuration Form (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Transaction Parameters
            </h3>
            <span className="text-[11px] font-mono text-slate-500">Real Backend Input</span>
          </div>

          <form onSubmit={handleRunSimulation} className="space-y-3.5 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">
                Amount (INR)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono font-bold focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Customer ID</label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Merchant ID</label>
                <input
                  type="text"
                  value={merchantId}
                  onChange={(e) => setMerchantId(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Device Fingerprint</label>
                <input
                  type="text"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">IP Address</label>
                <input
                  type="text"
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Country</label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
                >
                  <option value="upi">UPI</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="net_banking">Net Banking</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Attempts (Last 10m)</label>
                <input
                  type="number"
                  value={velocity10m}
                  onChange={(e) => setVelocity10m(Number(e.target.value))}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Attempts (Last 1h)</label>
                <input
                  type="number"
                  value={velocity1h}
                  onChange={(e) => setVelocity1h(Number(e.target.value))}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isNewDevice === 1}
                  onChange={(e) => setIsNewDevice(e.target.checked ? 1 : 0)}
                  className="rounded border-slate-800 text-blue-500 focus:ring-0"
                />
                <span className="text-slate-300">New Device</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isNewCountry === 1}
                  onChange={(e) => setIsNewCountry(e.target.checked ? 1 : 0)}
                  className="rounded border-slate-800 text-blue-500 focus:ring-0"
                />
                <span className="text-slate-300">New Country</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={running}
              className="w-full mt-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm shadow-blue-500/30"
            >
              <Play className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
              {running ? 'Executing Live Backend Pipeline...' : 'Execute Real-Time Risk Pipeline'}
            </button>
          </form>
        </div>

        {/* Live Pipeline Execution Resolution (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
              {error}
            </div>
          )}

          {!simulationResult && !running && (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 flex flex-col items-center justify-center min-h-[400px]">
              <div className="w-14 h-14 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                <Activity className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-white">Ready for Real-Time Simulation</h3>
              <p className="text-xs text-slate-400 max-w-md mt-1">
                Choose a preset scenario on the left or customize parameters, then click execute to watch the transaction traverse feature extraction, ML inference, behavioral baselining, and policy decision.
              </p>
            </div>
          )}

          {running && (
            <div className="p-12 text-center rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center min-h-[400px]">
              <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4"></div>
              <h3 className="text-sm font-bold text-white">Running Backend Engine Pipeline...</h3>
              <p className="text-xs text-slate-400 mt-1">
                Extracting 17 features, querying customer baseline, scoring XGBoost model, compiling evidence chain...
              </p>
            </div>
          )}

          {simulationResult && !running && (
            <div className="space-y-6">
              {/* Top Result Banner */}
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-5">
                  <RiskScoreGauge
                    score={simulationResult.result.risk_score}
                    level={simulationResult.result.risk_level}
                    size={100}
                  />
                  <div>
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                      Transaction ID: {simulationResult.transaction_id}
                    </span>
                    <h2 className="text-xl font-bold text-white mt-0.5">
                      Decision: <span className="text-blue-400">{simulationResult.result.decision}</span>
                    </h2>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-300">
                      <span>Confidence: <strong className="text-emerald-400 font-mono">{int(simulationResult.result.confidence_score * 100)}%</strong></span>
                      <span>•</span>
                      <span>Exposure: <strong className="text-white font-mono">₹{simulationResult.result.business_impact?.potential_loss_exposure?.toLocaleString()}</strong></span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/investigations/${simulationResult.transaction_id}`)}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-sm shadow-blue-500/20 shrink-0"
                >
                  Open Full Investigation <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              {/* Step-by-Step Pipeline Trace */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  Live Pipeline Execution Trace
                </h4>

                <div className="space-y-3">
                  {simulationResult.pipeline_trace.map((step) => (
                    <div
                      key={step.step}
                      className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/90 flex items-start gap-3"
                    >
                      <span className="w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                        {step.step}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-xs text-slate-200">
                            {step.title}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-semibold">
                            {step.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">{step.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function int(val: number): number {
  return Math.round(val);
}
