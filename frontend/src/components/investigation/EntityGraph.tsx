import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { LoadingState } from "@/components/common/States";
import type { EntityType, SubgraphEdge, SubgraphNode } from "@/api/types";

interface Props {
  rootType: EntityType;
  rootId: string;
}

const TYPE_COLOR: Record<EntityType, string> = {
  customer: "#3b82f6",
  device: "#8b5cf6",
  ip: "#ec4899",
  merchant: "#22d3ee",
};

const RISK_COLOR: Record<SubgraphNode["risk_hint"], string> = {
  root: "#f97316",
  high: "#dc2626",
  warning: "#eab308",
  neutral: "#5c6b7d",
};

export function EntityGraph({ rootType, rootId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["subgraph", rootType, rootId, 1],
    queryFn: () => api.getSubgraph(rootType, rootId, 1),
  });

  const layout = useMemo(() => (data ? computeLayout(data.nodes, data.edges, data.root.id) : null), [data]);

  if (isLoading) return <LoadingState label="Building entity graph…" />;
  if (!data || !layout) return <div className="text-sm text-ink-400">No related entities.</div>;

  const { positions, viewBox } = layout;

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-2xs text-ink-400">
        <span>Nodes: <span className="text-ink-200 tabular-nums">{data.stats.n_nodes}</span></span>
        <span>Edges: <span className="text-ink-200 tabular-nums">{data.stats.n_edges}</span></span>
        <span>Transactions: <span className="text-ink-200 tabular-nums">{data.stats.n_transactions}</span></span>
        <span className="ml-auto flex items-center gap-2">
          <LegendDot color={RISK_COLOR.root} label="Root" />
          <LegendDot color={RISK_COLOR.high} label="Hub" />
          <LegendDot color={RISK_COLOR.warning} label="Connector" />
        </span>
      </div>
      <svg viewBox={viewBox} className="h-[320px] w-full rounded-md border border-ink-700/60 bg-ink-950/40">
        {data.edges.map((e, i) => {
          const a = positions[e.source];
          const b = positions[e.target];
          if (!a || !b) return null;
          const opacity = Math.min(0.85, 0.25 + e.weight * 0.08);
          const width = Math.min(3, 0.6 + e.weight * 0.25);
          return (
            <line
              key={i}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke="#5c6b7d"
              strokeOpacity={opacity}
              strokeWidth={width}
            />
          );
        })}
        {data.nodes.map((n) => {
          const p = positions[n.id];
          if (!p) return null;
          const r = n.id === data.root.id ? 9 : 6;
          return (
            <g key={n.id} transform={`translate(${p.x}, ${p.y})`}>
              <circle
                r={r + 2}
                fill="none"
                stroke={RISK_COLOR[n.risk_hint]}
                strokeWidth={1.5}
                opacity={0.85}
              />
              <circle r={r} fill={TYPE_COLOR[n.type]} opacity={0.9} />
              <text
                x={0}
                y={r + 12}
                textAnchor="middle"
                fill="#c1cad4"
                fontSize={9}
                fontFamily="ui-monospace, monospace"
              >
                {n.label.length > 22 ? n.label.slice(0, 20) + "…" : n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="inline-block h-2 w-2 rounded-full ring-1 ring-inset" style={{ background: color, boxShadow: `0 0 0 1px ${color}` }} />
      {label}
    </span>
  );
}

function computeLayout(nodes: SubgraphNode[], edges: SubgraphEdge[], rootId: string) {
  // Cap at N nodes for a readable canvas.
  const MAX = 40;
  const byDegree = new Map<string, number>();
  edges.forEach((e) => {
    byDegree.set(e.source, (byDegree.get(e.source) || 0) + e.weight);
    byDegree.set(e.target, (byDegree.get(e.target) || 0) + e.weight);
  });
  const ranked = [...nodes]
    .sort((a, b) => {
      if (a.id === rootId) return -1;
      if (b.id === rootId) return 1;
      return (byDegree.get(b.id) || 0) - (byDegree.get(a.id) || 0);
    })
    .slice(0, MAX);

  const keep = new Set(ranked.map((n) => n.id));
  const visibleEdges = edges.filter((e) => keep.has(e.source) && keep.has(e.target));

  const W = 800;
  const H = 340;
  const cx = W / 2;
  const cy = H / 2;

  const positions: Record<string, { x: number; y: number }> = {};
  positions[rootId] = { x: cx, y: cy };

  // Ring layout: place others on a circle around the root.
  const others = ranked.filter((n) => n.id !== rootId);
  const R1 = Math.min(W, H) * 0.35;
  const R2 = Math.min(W, H) * 0.48;
  others.forEach((n, i) => {
    const angle = (i / Math.max(1, others.length)) * Math.PI * 2;
    const r = i % 2 === 0 ? R1 : R2;
    positions[n.id] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });

  return {
    positions,
    viewBox: `0 0 ${W} ${H}`,
    visibleEdges,
  };
}
