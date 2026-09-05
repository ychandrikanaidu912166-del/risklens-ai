import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Inbox,
  LineChart,
  Cpu,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Zap,
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-[#0B0F19] text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-[#0F172A]/70 backdrop-blur flex flex-col justify-between p-4 shrink-0">
        <div>
          {/* Logo & Title */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6 border-b border-slate-800/80">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">RiskLens</span>
                <span className="text-xs px-1.5 py-0.5 font-bold uppercase rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Payment Risk Intelligence</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <LayoutDashboard className="w-4 h-4" />
              Overview
            </NavLink>

            <NavLink
              to="/investigations"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Inbox className="w-4 h-4" />
              Investigation Queue
            </NavLink>

            <NavLink
              to="/simulation"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Zap className="w-4 h-4 text-amber-400" />
              Risk Simulator
            </NavLink>

            <NavLink
              to="/model-monitoring"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <LineChart className="w-4 h-4" />
              Model Monitoring
            </NavLink>
          </nav>
        </div>

        {/* System Status Pill in Sidebar */}
        <div className="pt-4 border-t border-slate-800/80 space-y-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Engine Status
              </span>
              <span className="font-mono text-[10px] text-emerald-400 uppercase font-semibold">Live</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-300">
              <span>ML Classifier:</span>
              <span className="font-mono text-blue-400 font-semibold">v1.2.0-xgb</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-300 mt-1">
              <span>Decision Policy:</span>
              <span className="font-mono text-purple-400 font-semibold">v2.4-enterprise</span>
            </div>
          </div>

          <div className="flex items-center gap-2 px-2 text-slate-500 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
            <span>Razorpay Risk Challenge</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 bg-[#0F172A]/40 backdrop-blur px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
              OPERATIONAL ENVIRONMENT
            </span>
            <span className="text-xs text-slate-400">
              Deterministic Evidence &amp; AI-Assisted Fraud Investigation
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs font-semibold text-slate-200">Risk Operations Desk</div>
              <div className="text-[10px] font-mono text-slate-400">analyst_lead_01</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center font-bold text-xs text-blue-300">
              RO
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
