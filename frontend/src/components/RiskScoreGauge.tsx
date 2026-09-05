import React from 'react';

interface RiskScoreGaugeProps {
  score: number;
  level: string;
  size?: number;
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({ score, level, size = 120 }) => {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  let color = '#10B981'; // LOW: emerald
  let textColor = 'text-emerald-400';
  let badgeBg = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';

  if (score >= 85 || level === 'CRITICAL') {
    color = '#EF4444'; // CRITICAL: red
    textColor = 'text-red-400';
    badgeBg = 'bg-red-500/10 border-red-500/30 text-red-400 animate-pulse';
  } else if (score >= 60 || level === 'HIGH') {
    color = '#F97316'; // HIGH: orange
    textColor = 'text-orange-400';
    badgeBg = 'bg-orange-500/10 border-orange-500/30 text-orange-400';
  } else if (score >= 30 || level === 'MEDIUM') {
    color = '#F59E0B'; // MEDIUM: amber
    textColor = 'text-amber-400';
    badgeBg = 'bg-amber-500/10 border-amber-500/30 text-amber-300';
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1F2937"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Active progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-extrabold font-mono tracking-tight ${textColor}`}>
            {score}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            / 100
          </span>
        </div>
      </div>
      <div className="mt-2">
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border ${badgeBg}`}>
          {level} RISK
        </span>
      </div>
    </div>
  );
};
