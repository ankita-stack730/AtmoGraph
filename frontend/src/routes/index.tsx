import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowRight, Radar, Waves, Zap } from "lucide-react";
import { useState } from "react";
import { SAMPLE_DISRUPTION } from "@/api/client";
import { useGraph, useHealth } from "@/components/atmo/useHealth";
import { Kpi, Panel } from "@/components/atmo/ui";
import { runDisruptionAnalysis } from "@/lib/analyze";
import { useAtmoStore } from "@/lib/store";
import { colorForLabel, labelOf } from "@/lib/risk";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ATMOgraph — Supply Chain Ripple Effect Intelligence" },
      {
        name: "description",
        content:
          "See the ripple. Predict the impact. Operational command center for supply chain disruption propagation across ports, suppliers, plants and products.",
      },
      { property: "og:title", content: "ATMOgraph — Supply Chain Ripple Intelligence" },
      {
        property: "og:description",
        content: "Trace disruption ripple effects across your supply chain graph in real time.",
      },
    ],
  }),
  component: Overview,
});

function Overview() {
  const { data: graph } = useGraph();
  const { data: health } = useHealth();
  const { analyzing, disruption } = useAtmoStore();
  const [text, setText] = useState(SAMPLE_DISRUPTION);
  const navigate = useNavigate();

  const nodes = graph?.data.nodes ?? [];
  const rels = graph?.data.relationships ?? [];
  const byLabel = nodes.reduce<Record<string, number>>((acc, n) => {
    const l = labelOf(n.labels as string[]);
    acc[l] = (acc[l] ?? 0) + 1;
    return acc;
  }, {});

  async function analyze() {
    await runDisruptionAnalysis(text);
    navigate({ to: "/disruptions" });
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      <section className="grid-backdrop relative overflow-hidden rounded-xl border border-border bg-card p-6 md:p-8">
        <div className="absolute -right-24 -top-24 size-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-primary">
            <Radar className="size-3" /> Ripple Effect Intelligence
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">
            See the ripple. Predict the impact.
          </h1>
          <p className="mt-3 text-sm text-muted-foreground">
            ATMOgraph reads a disruption in plain language, matches it to your supply chain graph,
            and propagates risk hop by hop across ports, suppliers, plants, products and customers.
          </p>

          <div className="mt-6 rounded-lg border border-border bg-background/60 p-3">
            <label className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Quick disruption analyze
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={2}
              className="mt-2 w-full resize-none rounded-md border border-border bg-card p-3 font-mono text-xs outline-none focus:border-primary/60"
            />
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <button
                onClick={analyze}
                disabled={analyzing}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
              >
                <Zap className="size-3.5" />
                {analyzing ? "Propagating…" : "Run ripple analysis"}
              </button>
              <button
                onClick={() => setText(SAMPLE_DISRUPTION)}
                className="rounded-md border border-border px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                Load sample
              </button>
              <Link
                to="/network"
                className="ml-auto inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest text-primary"
              >
                Open network <ArrowRight className="size-3" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Graph nodes" value={nodes.length} hint="Entities in the active topology" />
        <Kpi label="Relationships" value={rels.length} hint="Directed supply chain edges" />
        <Kpi
          label="Affected nodes"
          value={disruption?.affected_nodes ?? "—"}
          hint="From last ripple run"
          tone="primary"
        />
        <Kpi
          label="High-risk nodes"
          value={disruption?.high_risk_nodes ?? "—"}
          hint="Risk score ≥ 0.70"
          tone="danger"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Network summary" className="lg:col-span-2">
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(byLabel).map(([label, count]) => (
              <div
                key={label}
                className="flex items-center gap-3 rounded-md border border-border px-3 py-2"
              >
                <span className="size-2 rounded-full" style={{ background: colorForLabel(label) }} />
                <span className="text-xs">{label}</span>
                <span className="ml-auto font-mono text-xs tabular-nums text-muted-foreground">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Engine posture">
          <ul className="space-y-3 text-xs">
            <li className="flex items-center justify-between">
              <span className="text-muted-foreground">FastAPI</span>
              <span className="font-mono text-[11px]">
                {health?.source === "live" ? "connected" : "unreachable"}
              </span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-muted-foreground">Graph baseline</span>
              <span className="font-mono text-[11px] text-risk-low">active</span>
            </li>
            <li className="flex items-center justify-between">
              <span className="text-muted-foreground">GNN engine</span>
              <span className="font-mono text-[11px] text-risk-medium">not connected</span>
            </li>
            <li className="flex items-center gap-2 pt-1">
              <Waves className="size-3.5 text-primary" />
              <span className="text-muted-foreground">
                Method: <span className="font-mono">GRAPH_BASELINE</span>
              </span>
            </li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
