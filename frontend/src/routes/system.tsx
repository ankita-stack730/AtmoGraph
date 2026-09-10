import { createFileRoute } from "@tanstack/react-router";
import { RefreshCw } from "lucide-react";
import { API_BASE_URL } from "@/api/client";
import { useGraph, useHealth } from "@/components/atmo/useHealth";
import { PageHeader, Panel } from "@/components/atmo/ui";
import { useAtmoStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/system")({
  head: () => ({
    meta: [
      { title: "System Status — ATMOgraph" },
      {
        name: "description",
        content:
          "Live telemetry for the FastAPI service, Neo4j graph store, NLP pipeline, graph engine and GNN prediction engine.",
      },
      { property: "og:title", content: "System Status — ATMOgraph" },
      {
        property: "og:description",
        content: "Component-level health of the ATMOgraph intelligence stack.",
      },
    ],
  }),
  component: SystemPage,
});

type State = "ok" | "degraded" | "down";

function StatusRow({
  name,
  endpoint,
  state,
  detail,
}: {
  name: string;
  endpoint: string;
  state: State;
  detail: string;
}) {
  const tone = {
    ok: "text-risk-low border-risk-low/40 bg-risk-low/10",
    degraded: "text-risk-medium border-risk-medium/40 bg-risk-medium/10",
    down: "text-risk-critical border-risk-critical/40 bg-risk-critical/10",
  }[state];
  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3 last:border-0">
      <span className={cn("size-2 rounded-full", state === "ok" ? "bg-risk-low" : state === "degraded" ? "bg-risk-medium" : "bg-risk-critical")} />
      <div className="min-w-40">
        <div className="text-sm">{name}</div>
        <div className="font-mono text-[10px] text-muted-foreground">{endpoint}</div>
      </div>
      <div className="flex-1 text-xs text-muted-foreground">{detail}</div>
      <span
        className={cn(
          "rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
          tone,
        )}
      >
        {state}
      </span>
    </div>
  );
}

function SystemPage() {
  const health = useHealth();
  const graph = useGraph();
  const { disruption } = useAtmoStore();
  const live = health.data?.source === "live";

  return (
    <div>
      <PageHeader
        title="System status"
        subtitle="Component telemetry for the ATMOgraph intelligence stack."
        right={
          <button
            onClick={() => {
              void health.refetch();
              void graph.refetch();
            }}
            className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={cn("size-3", health.isFetching && "animate-spin")} /> Refresh
          </button>
        }
      />

      <div className="space-y-4 p-4 md:p-6">
        <Panel title={`Base URL · ${API_BASE_URL}`} className="p-0">
          <div className="-m-4">
            <StatusRow
              name="FastAPI service"
              endpoint="GET /health"
              state={live ? "ok" : "down"}
              detail={
                live
                  ? `Responding — status "${health.data?.data.status ?? "unknown"}"`
                  : "Unreachable. UI is serving baseline demo data."
              }
            />
            <StatusRow
              name="Neo4j graph store"
              endpoint="GET /graph"
              state={graph.data?.source === "live" ? "ok" : "down"}
              detail={`${graph.data?.data.nodes.length ?? 0} nodes · ${graph.data?.data.relationships.length ?? 0} relationships loaded`}
            />
            <StatusRow
              name="NLP pipeline"
              endpoint="POST /nlp/analyze"
              state={live ? "ok" : "degraded"}
              detail={
                live
                  ? "Entity extraction and disruption classification online."
                  : "Local keyword matcher in use while backend is offline."
              }
            />
            <StatusRow
              name="Graph baseline engine"
              endpoint="POST /disruption/analyze"
              state="ok"
              detail={`Method ${disruption?.method ?? "GRAPH_BASELINE"} · hop-distance propagation active.`}
            />
            <StatusRow
              name="GNN prediction engine"
              endpoint="predictions[]"
              state="degraded"
              detail="Not connected — no learned predictions or confidence values are produced."
            />
          </div>
        </Panel>

        <Panel title="Last raw health payload">
          <pre className="overflow-x-auto rounded-md border border-border bg-background p-3 font-mono text-[11px] text-muted-foreground">
            {JSON.stringify(health.data?.data ?? {}, null, 2)}
          </pre>
          {health.data?.error && (
            <p className="mt-2 font-mono text-[10px] text-risk-high">
              transport: {health.data.error}
            </p>
          )}
        </Panel>
      </div>
    </div>
  );
}
