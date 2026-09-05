import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { LoadingState, ErrorState, EmptyState } from "@/components/common/States";
import { formatDateTime } from "@/components/common/format";
import { PageHeader } from "./Overview";

export function Audit() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["audit"],
    queryFn: () => api.listAudit({ limit: 200 }),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Audit trail" subtitle="Append-only record of scoring events and analyst decisions." />

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState title="Could not load audit trail" detail={String(error)} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No audit events yet" detail="Score a transaction or record an analyst decision to populate the trail." />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-700/60 text-2xs uppercase tracking-wider text-ink-400">
                <th className="px-4 py-2 text-left font-medium">Time</th>
                <th className="px-4 py-2 text-left font-medium">Actor</th>
                <th className="px-4 py-2 text-left font-medium">Action</th>
                <th className="px-4 py-2 text-left font-medium">Entity</th>
                <th className="px-4 py-2 text-left font-medium">Payload</th>
              </tr>
            </thead>
            <tbody>
              {data.map((e) => (
                <tr key={e.id} className="border-b border-ink-800/70 last:border-0 hover:bg-ink-800/40">
                  <td className="px-4 py-2 text-xs text-ink-400 tabular-nums whitespace-nowrap">{formatDateTime(e.created_at)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-ink-300">{e.actor}</td>
                  <td className="px-4 py-2">
                    <code className="rounded bg-ink-800/70 px-1.5 py-0.5 text-2xs text-ink-100">{e.action}</code>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-ink-300">
                    <span className="text-ink-500">{e.entity_type}:</span>{e.entity_id}
                  </td>
                  <td className="px-4 py-2 text-xs text-ink-300">
                    {e.payload_json ? (
                      <code className="block max-w-md truncate rounded bg-ink-800/60 px-2 py-0.5 text-2xs">
                        {JSON.stringify(e.payload_json)}
                      </code>
                    ) : (
                      <span className="text-ink-500">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
