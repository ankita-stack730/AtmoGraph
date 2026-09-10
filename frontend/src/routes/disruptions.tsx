import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, ChevronRight, CircleCheck, Loader2, Zap } from "lucide-react";
import { useState } from "react";
import { SAMPLE_DISRUPTION } from "@/api/client";
import { Panel } from "@/components/atmo/ui";
import { runDisruptionAnalysis } from "@/lib/analyze";
import { useAtmoStore } from "@/lib/store";
import { RISK_BADGE, RISK_HEX, riskBand, severityBand } from "@/lib/risk";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/disruptions")({
  head: () => ({
    meta: [
      { title: "Disruption Analysis — ATMOgraph" },
      {
        name: "description",
        content:
          "Analyze a disruption in plain language, extract entities, match graph nodes and propagate risk hop by hop.",
      },
      { property: "og:title", content: "Disruption Analysis — ATMOgraph" },
      {
        property: "og:description",
        content: "From free text to ripple propagation across the supply chain graph.",
      },
    ],
  }),
  component: DisruptionsPage,
});

const STEPS = ["Ingest text", "NLP entities", "Graph match", "Ripple propagation", "Scoring"];

function DisruptionsPage() {
  const { disruption, analyzing, disruptionSource } = useAtmoStore();
  const [text, setText] = useState(SAMPLE_DISRUPTION);

  const stepsDone = analyzing ? 2 : disruption ? STEPS.length : 0;
  const sev = disruption ? severityBand(disruption.event.severity) : null;

  const groups = new Map<number, typeof disruption extends null ? never : NonNullable<typeof disruption>["nodes"]>();
  disruption?.nodes.forEach((n) => {
    groups.set(n.hop_distance, [...(groups.get(n.hop_distance) ?? []), n]);
  });

  return (
    <div className="space-y-6 p-4 md:p-6">
      <Panel title="Disruption input">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="Describe the disruption event…"
          className="w-full resize-none rounded-md border border-border bg-background p-3 font-mono text-xs outline-none focus:border-primary/60"
        />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            onClick={() => void runDisruptionAnalysis(text)}
            disabled={analyzing}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {analyzing ? <Loader2 className="size-3.5 animate-spin" /> : <Zap className="size-3.5" />}
            {analyzing ? "Analyzing…" : "Analyze disruption"}
          </button>
          <button
            onClick={() => setText(SAMPLE_DISRUPTION)}
            className="rounded-md border border-border px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
          >
            Preset sample
          </button>
          {disruptionSource && (
            <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              source: {disruptionSource === "live" ? "POST /disruption/analyze" : "baseline mock"}
            </span>
          )}
        </div>

        <ol className="mt-5 grid gap-2 sm:grid-cols-5">
          {STEPS.map((s, i) => {
            const done = i < stepsDone;
            return (
              <li
                key={s}
                className={cn(
                  "flex items-center gap-2 rounded-md border px-3 py-2 font-mono text-[10px] uppercase tracking-widest",
                  done
                    ? "border-primary/40 bg-primary/5 text-primary"
                    : "border-border text-muted-foreground",
                )}
              >
                {done ? <CircleCheck className="size-3" /> : <span>{i + 1}</span>}
                {s}
              </li>
            );
          })}
        </ol>
      </Panel>

      {!disruption && !analyzing && (
        <div className="rounded-lg border border-dashed border-border p-10 text-center font-mono text-xs text-muted-foreground">
          No analysis yet — run a disruption to populate the ripple tree.
        </div>
      )}

      {disruption && (
        <>
          <div
            className={cn(
              "flex flex-wrap items-center gap-4 rounded-lg border p-4",
              sev ? RISK_BADGE[sev] : "border-border",
            )}
          >
            <AlertTriangle className="size-5" />
            <div>
              <div className="font-mono text-sm font-semibold uppercase tracking-widest">
                {disruption.event.type}
              </div>
              <div className="text-xs opacity-80">
                Severity {disruption.event.severity} · method {disruption.method}
              </div>
            </div>
            <div className="ml-auto flex gap-6 font-mono text-xs">
              <div>
                <div className="text-[10px] uppercase opacity-70">Affected</div>
                <div className="text-lg tabular-nums">{disruption.affected_nodes}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase opacity-70">High risk</div>
                <div className="text-lg tabular-nums">{disruption.high_risk_nodes}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase opacity-70">Sources</div>
                <div className="text-lg tabular-nums">
                  {disruption.matched_source_nodes.length}
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Panel title="NLP entities">
              <div className="flex flex-wrap gap-2">
                {disruption.entities.map((e, i) => (
                  <span
                    key={`${e.text}-${i}`}
                    className="rounded-md border border-border bg-background px-2.5 py-1.5"
                  >
                    <span className="text-xs">{e.text}</span>
                    <span className="ml-2 font-mono text-[9px] uppercase tracking-widest text-primary">
                      {e.type}
                    </span>
                    <span className="ml-2 font-mono text-[9px] text-muted-foreground">
                      {e.matched_node_id ?? "unmatched"}
                    </span>
                  </span>
                ))}
                {!disruption.entities.length && (
                  <span className="font-mono text-xs text-muted-foreground">
                    No entities extracted.
                  </span>
                )}
              </div>
              <Link
                to="/network"
                className="mt-4 inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest text-primary"
              >
                Focus graph on impact <ChevronRight className="size-3" />
              </Link>
            </Panel>

            <Panel title="Risk propagation tree" className="lg:col-span-2">
              <div className="space-y-4">
                {[...groups.entries()]
                  .sort((a, b) => a[0] - b[0])
                  .map(([hop, nodes]) => (
                    <div key={hop}>
                      <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        Hop {hop} · {nodes.length} node{nodes.length === 1 ? "" : "s"}
                      </div>
                      <div className="space-y-1 border-l border-border pl-4">
                        {nodes.map((n) => {
                          const band = riskBand(n.risk_score);
                          return (
                            <div
                              key={n.node_id}
                              className="flex items-center gap-3 rounded-md border border-border bg-background px-3 py-2"
                            >
                              <span
                                className="size-2 rounded-full"
                                style={{ background: RISK_HEX[band] }}
                              />
                              <span className="truncate text-xs">{n.name}</span>
                              <span className="font-mono text-[9px] uppercase text-muted-foreground">
                                {n.labels[0]}
                              </span>
                              {n.is_source && (
                                <span className="rounded bg-primary/15 px-1.5 font-mono text-[9px] uppercase text-primary">
                                  source
                                </span>
                              )}
                              <span
                                className="ml-auto font-mono text-xs tabular-nums"
                                style={{ color: RISK_HEX[band] }}
                              >
                                {n.risk_score.toFixed(2)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
              </div>
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
