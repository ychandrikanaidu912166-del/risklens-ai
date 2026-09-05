import type { RiskLevel } from "@/api/types";

const COLOR_BY_LEVEL: Record<RiskLevel, string> = {
  LOW: "#16a34a",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#dc2626",
};

interface Props {
  score: number;
  level: RiskLevel;
  size?: number;
}

export function ScoreDial({ score, level, size = 168 }: Props) {
  const radius = size / 2 - 12;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);
  const color = COLOR_BY_LEVEL[level];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgb(37 49 63 / 0.7)"
          strokeWidth={10}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-4xl font-semibold tabular-nums text-ink-100">{clamped}</div>
        <div className="text-2xs uppercase tracking-wider text-ink-400">Risk Score / 100</div>
      </div>
    </div>
  );
}
