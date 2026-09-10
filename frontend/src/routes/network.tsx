import { createFileRoute } from "@tanstack/react-router";
import { ClientOnly } from "@tanstack/react-router";
import { Suspense, lazy, useMemo, useState } from "react";
import { useGraph } from "@/components/atmo/useHealth";
import { NodeInspector } from "@/components/atmo/NodeInspector";
import { useAtmoStore } from "@/lib/store";
import { colorForLabel, labelOf, RISK_HEX } from "@/lib/risk";
import { cn } from "@/lib/utils";

const GraphCanvas = lazy(() => import("@/components/atmo/GraphCanvas"));

export const Route = createFileRoute("/network")({
  head: () => ({
    meta: [
      { title: "Network Graph — ATMOgraph" },
      {
        name: "description",
        content:
          "Interactive supply chain network graph: ports, suppliers, manufacturers, warehouses, products and routes with live risk halos.",
      },
      { property: "og:title", content: "Network Graph — ATMOgraph" },
      {
        property: "og:description",
        content: "Explore the supply chain topology and inspect any node in detail.",
      },
    ],
  }),
  component: NetworkPage,
});

const ALL_LABELS = [
  "Port",
  "Supplier",
  "Manufacturer",
  "Warehouse",
  "Product",
  "Company",
  "Country",
  "ShippingRoute",
];

function NetworkPage() {
  const { data, isLoading } = useGraph();
  const { disruption } = useAtmoStore();
  const [selected, setSelected] = useState<string | null>(null);
  const [labels, setLabels] = useState<string[]>(ALL_LABELS);
  const [highlightOnly, setHighlightOnly] = useState(true);

  const riskById = useMemo(() => {
    const map: Record<string, number> = {};
    disruption?.nodes.forEach((n) => (map[n.node_id] = n.risk_score));
    return map;
  }, [disruption]);

  const graph = data?.data;

  return (
    <div className="relative h-[calc(100vh-57px)] overflow-hidden">
      <div className="absolute inset-x-0 top-0 z-10 flex flex-wrap items-center gap-2 border-b border-border bg-background/85 px-4 py-2.5 backdrop-blur">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Filters
        </span>
        {ALL_LABELS.map((l) => {
          const on = labels.includes(l);
          return (
            <button
              key={l}
              onClick={() =>
                setLabels((prev) => (on ? prev.filter((x) => x !== l) : [...prev, l]))
              }
              className={cn(
                "rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest transition",
                on ? "text-foreground" : "border-border text-muted-foreground opacity-50",
              )}
              style={on ? { borderColor: colorForLabel(l), color: colorForLabel(l) } : undefined}
            >
              {l}
            </button>
          );
        })}
        {disruption && (
          <label className="ml-auto flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <input
              type="checkbox"
              checked={highlightOnly}
              onChange={(e) => setHighlightOnly(e.target.checked)}
              className="accent-[#00f0ff]"
            />
            Dim unaffected
          </label>
        )}
      </div>

      <div className="absolute inset-0 pt-12">
        {isLoading || !graph ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground">
            Loading topology…
          </div>
        ) : (
          <ClientOnly
            fallback={
              <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground">
                Initialising canvas…
              </div>
            }
          >
            <Suspense
              fallback={
                <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground">
                  Initialising canvas…
                </div>
              }
            >
              <GraphCanvas
                graph={graph}
                riskById={riskById}
                sourceIds={disruption?.matched_source_nodes ?? []}
                visibleLabels={labels}
                highlightOnly={Boolean(disruption) && highlightOnly}
                onSelect={setSelected}
              />
            </Suspense>
          </ClientOnly>
        )}
      </div>

      <div className="pointer-events-none absolute bottom-4 left-4 z-10 rounded-lg border border-border bg-card/90 p-3 backdrop-blur">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Legend
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {ALL_LABELS.map((l) => (
            <div key={l} className="flex items-center gap-2 text-[10px]">
              <span className="size-2 rounded-full" style={{ background: colorForLabel(l) }} />
              {l}
            </div>
          ))}
        </div>
        <div className="mt-2 flex items-center gap-3 border-t border-border pt-2">
          {(["low", "medium", "high", "critical"] as const).map((b) => (
            <div key={b} className="flex items-center gap-1.5 text-[10px] capitalize">
              <span className="size-2 rounded-full" style={{ background: RISK_HEX[b] }} />
              {b}
            </div>
          ))}
        </div>
      </div>

      {graph && (
        <div className="pointer-events-none absolute right-4 top-16 z-10 rounded-md border border-border bg-card/90 px-3 py-2 font-mono text-[10px] text-muted-foreground backdrop-blur">
          {graph.nodes.filter((n) => labels.includes(labelOf(n.labels as string[]))).length} nodes ·{" "}
          {graph.relationships.length} edges
        </div>
      )}

      <NodeInspector nodeId={selected} onClose={() => setSelected(null)} onSelect={setSelected} />
    </div>
  );
}
