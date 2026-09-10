import { createFileRoute, Link } from "@tanstack/react-router";
import { BrainCircuit, GitBranch, PlugZap } from "lucide-react";
import { Panel } from "@/components/atmo/ui";
import { useAtmoStore } from "@/lib/store";
import { RISK_HEX, riskBand } from "@/lib/risk";

export const Route = createFileRoute("/predictions")({
  head: () => ({
    meta: [
      { title: "Predictions — ATMOgraph" },
      {
        name: "description",
        content:
          "Graph baseline propagation results and the honest status of the GNN prediction engine.",
      },
      { property: "og:title", content: "Predictions — ATMOgraph" },
      {
        property: "og:description",
        content: "Graph baseline active; GNN prediction engine reported as not connected.",
      },
    ],
  }),
  component: PredictionsPage,
});

function PredictionsPage() {
  const { disruption } = useAtmoStore();
  const top = (disruption?.nodes ?? []).slice(0, 12);

  return (
    <div className="grid gap-4 p-4 lg:grid-cols-2 md:p-6">
      <Panel
        title="Graph baseline engine"
        action={
          <span className="rounded-full border border-risk-low/40 bg-risk-low/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-risk-low">
            Active
          </span>
        }
      >
        <div className="flex items-start gap-3">
          <GitBranch className="mt-0.5 size-4 text-primary" />
          <p className="text-xs text-muted-foreground">
            Deterministic hop-distance propagation over the Neo4j topology. Risk decays with each
            hop from the matched source nodes. Method identifier:{" "}
            <span className="font-mono text-foreground">GRAPH_BASELINE</span>.
          </p>
        </div>

        <div className="mt-4 space-y-1">
          {top.map((n) => {
            const band = riskBand(n.risk_score);
            return (
              <div
                key={n.node_id}
                className="flex items-center gap-3 rounded-md border border-border px-3 py-2"
              >
                <span className="size-2 rounded-full" style={{ background: RISK_HEX[band] }} />
                <span className="truncate text-xs">{n.name}</span>
                <span className="font-mono text-[9px] uppercase text-muted-foreground">
                  hop {n.hop_distance}
                </span>
                <span
                  className="ml-auto font-mono text-xs tabular-nums"
                  style={{ color: RISK_HEX[band] }}
                >
                  {n.risk_score.toFixed(2)}
                </span>
              </div>
            );
          })}
          {!top.length && (
            <div className="rounded-md border border-dashed border-border p-6 text-center font-mono text-xs text-muted-foreground">
              No baseline output yet.{" "}
              <Link to="/disruptions" className="text-primary">
                Run a disruption analysis
              </Link>
              .
            </div>
          )}
        </div>
      </Panel>

      <Panel
        title="GNN prediction engine"
        action={
          <span className="rounded-full border border-risk-medium/40 bg-risk-medium/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-risk-medium">
            Not connected
          </span>
        }
      >
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-border p-8 text-center">
          <BrainCircuit className="size-8 text-muted-foreground" />
          <h4 className="mt-3 text-sm font-semibold">GNN prediction engine not connected</h4>
          <p className="mt-2 max-w-sm text-xs text-muted-foreground">
            The backend returned <span className="font-mono">predictions: []</span>. No learned
            confidence scores, delay forecasts or embeddings are available. Nothing on this screen
            is inferred or simulated.
          </p>
          <div className="mt-4 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <PlugZap className="size-3" /> Awaiting model service registration
          </div>
        </div>

        <dl className="mt-4 divide-y divide-border rounded-md border border-border font-mono text-[11px]">
          {[
            ["predictions", `${disruption?.predictions.length ?? 0} returned`],
            ["model_version", "unavailable"],
            ["confidence", "unavailable"],
            ["method", disruption?.method ?? "GRAPH_BASELINE"],
          ].map(([k, v]) => (
            <div key={k} className="flex items-center justify-between px-3 py-2">
              <dt className="text-muted-foreground">{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </Panel>
    </div>
  );
}
