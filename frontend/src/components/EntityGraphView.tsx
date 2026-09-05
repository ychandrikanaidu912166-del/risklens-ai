import React, { useState } from 'react';
import { EntityGraph, EntityNode } from '../types';
import { Smartphone, Globe, User, Store, CreditCard, ShieldAlert, AlertTriangle } from 'lucide-react';

interface EntityGraphViewProps {
  graph: EntityGraph;
}

export const EntityGraphView: React.FC<EntityGraphViewProps> = ({ graph }) => {
  const [selectedNode, setSelectedNode] = useState<EntityNode | null>(null);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'transaction': return <CreditCard className="w-4 h-4 text-blue-400" />;
      case 'customer': return <User className="w-4 h-4 text-emerald-400" />;
      case 'device': return <Smartphone className="w-4 h-4 text-purple-400" />;
      case 'ip': return <Globe className="w-4 h-4 text-cyan-400" />;
      case 'merchant': return <Store className="w-4 h-4 text-amber-400" />;
      default: return <User className="w-4 h-4 text-slate-400" />;
    }
  };

  const getNodeBadgeClass = (risk: string) => {
    switch (risk) {
      case 'target':
        return 'border-blue-500 bg-blue-500/10 text-blue-200 shadow-sm shadow-blue-500/20';
      case 'suspicious':
        return 'border-red-500 bg-red-500/15 text-red-300 shadow-sm shadow-red-500/30 animate-pulse';
      case 'warning':
        return 'border-amber-500 bg-amber-500/10 text-amber-300';
      default:
        return 'border-slate-700 bg-slate-800/80 text-slate-300 hover:border-slate-600';
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            Entity Correlation Map
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-entity relationships identifying shared hardware, proxy infrastructure, and multi-accounting.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Current Txn
          </span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Shared Syndicate Link
          </span>
        </div>
      </div>

      {/* Nodes visual cluster */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 my-4">
        {graph.nodes.map((node) => {
          const isSelected = selectedNode?.id === node.id;
          return (
            <button
              key={node.id}
              onClick={() => setSelectedNode(node)}
              className={`flex flex-col items-start p-3 rounded-lg border text-left transition-all ${getNodeBadgeClass(node.risk)} ${isSelected ? 'ring-2 ring-blue-400' : ''}`}
            >
              <div className="flex items-center justify-between w-full mb-1.5">
                <span className="p-1.5 rounded-md bg-slate-950/60">{getNodeIcon(node.type)}</span>
                <span className="text-[10px] uppercase tracking-wider font-mono text-slate-400">
                  {node.type}
                </span>
              </div>
              <span className="font-mono text-xs font-medium truncate w-full" title={node.label}>
                {node.label}
              </span>
              {node.risk === 'suspicious' && (
                <span className="mt-1.5 inline-flex items-center gap-1 text-[10px] text-red-400 font-semibold">
                  <ShieldAlert className="w-3 h-3" /> Syndicate Node
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Relationships connection table */}
      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <h5 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
          Linked Relationships ({graph.edges.length})
        </h5>
        <div className="flex flex-wrap gap-2">
          {graph.edges.map((edge, idx) => (
            <div
              key={idx}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/60 text-xs font-mono text-slate-300"
            >
              <span className="text-slate-400 truncate max-w-[100px]">{edge.source}</span>
              <span className="text-[10px] text-blue-400 font-sans font-semibold">
                ─[{edge.label}]─▶
              </span>
              <span className="text-slate-200 truncate max-w-[100px]">{edge.target}</span>
            </div>
          ))}
        </div>
      </div>

      {selectedNode && (
        <div className="mt-4 p-3 rounded-lg bg-slate-950/70 border border-blue-500/30 flex items-center justify-between text-xs">
          <div>
            <span className="text-slate-400">Selected Entity: </span>
            <span className="font-mono text-blue-300 font-semibold">{selectedNode.label}</span>
            <span className="ml-2 text-slate-400">Type: </span>
            <span className="font-semibold text-slate-200 uppercase">{selectedNode.type}</span>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-slate-400 hover:text-slate-200"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};
