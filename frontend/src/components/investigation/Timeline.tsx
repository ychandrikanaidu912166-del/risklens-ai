import type { TimelineEvent } from "@/api/types";
import { formatDateTime } from "@/components/common/format";

export function Timeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0)
    return <div className="text-sm text-ink-400">No timeline events recorded.</div>;

  const sorted = [...events].sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
  return (
    <ol className="relative ml-3 space-y-4 border-l border-ink-700/60 pl-6">
      {sorted.map((ev, i) => (
        <li key={i} className="relative">
          <span className="absolute -left-[27px] top-1.5 h-2 w-2 rounded-full bg-brand-500 ring-4 ring-ink-950" />
          <div className="text-2xs uppercase tracking-wider text-ink-400">
            {formatDateTime(ev.ts)}
          </div>
          <div className="mt-0.5 text-sm font-medium text-ink-100">{ev.event.replace(/_/g, " ")}</div>
          <div className="mt-0.5 text-xs text-ink-400">{ev.detail}</div>
        </li>
      ))}
    </ol>
  );
}
