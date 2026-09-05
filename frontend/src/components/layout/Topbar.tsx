import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { CircleDot } from "lucide-react";

export function Topbar() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    refetchInterval: 60_000,
  });

  const ok = data?.status === "ok" && !isError;
  const dot = ok ? "text-risk-low" : "text-risk-critical";
  const label = isError
    ? "API unreachable"
    : data
    ? `${data.status.toUpperCase()} · ${data.model.model_kind ?? "no model"} · ${data.model.model_version ?? ""}`
    : "checking…";

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-ink-800 bg-ink-950/60 px-6">
      <div className="flex items-center gap-2 text-sm text-ink-300">
        <CircleDot className={`h-3 w-3 ${dot}`} />
        <span className="tabular-nums">{label}</span>
      </div>
      <div className="text-xs text-ink-500">
        Analyst: <span className="text-ink-200">demo</span>
      </div>
    </header>
  );
}
