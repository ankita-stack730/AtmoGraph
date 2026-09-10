import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useGraph } from "@/components/atmo/useHealth";
import { NodeInspector } from "@/components/atmo/NodeInspector";
import { PageHeader } from "@/components/atmo/ui";
import { colorForLabel, labelOf } from "@/lib/risk";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/entities")({
  validateSearch: (search: Record<string, unknown>) => ({
    q: typeof search["q"] === "string" ? (search["q"] as string) : "",
  }),
  head: () => ({
    meta: [
      { title: "Entity Directory — ATMOgraph" },
      {
        name: "description",
        content:
          "Searchable directory of every supply chain entity: ports, suppliers, manufacturers, warehouses, products, companies, countries and routes.",
      },
      { property: "og:title", content: "Entity Directory — ATMOgraph" },
      {
        property: "og:description",
        content: "Search and filter every node in the supply chain graph.",
      },
    ],
  }),
  component: EntitiesPage,
});

function EntitiesPage() {
  const { q } = Route.useSearch();
  const { data } = useGraph();
  const [query, setQuery] = useState(q);
  const [filter, setFilter] = useState<string>("All");
  const [selected, setSelected] = useState<string | null>(null);

  const nodes = data?.data.nodes ?? [];
  const labels = useMemo(
    () => ["All", ...new Set(nodes.map((n) => labelOf(n.labels as string[])))],
    [nodes],
  );

  const filtered = nodes.filter((n) => {
    const label = labelOf(n.labels as string[]);
    const matchesLabel = filter === "All" || label === filter;
    const text = `${n.name} ${n.node_id} ${label}`.toLowerCase();
    return matchesLabel && text.includes(query.trim().toLowerCase());
  });

  return (
    <div className="relative min-h-[calc(100vh-57px)]">
      <PageHeader
        title="Entity directory"
        subtitle="Every node in the active supply chain topology."
        right={
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {filtered.length} / {nodes.length} entities
          </span>
        }
      />

      <div className="space-y-4 p-4 md:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by name or node id…"
              className="w-full rounded-md border border-border bg-card py-2 pl-9 pr-3 font-mono text-xs outline-none focus:border-primary/60"
            />
          </div>
          {labels.map((l) => (
            <button
              key={l}
              onClick={() => setFilter(l)}
              className={cn(
                "rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest",
                filter === l
                  ? "border-primary/50 bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {l}
            </button>
          ))}
        </div>

        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((n) => {
            const label = labelOf(n.labels as string[]);
            return (
              <button
                key={n.node_id}
                onClick={() => setSelected(n.node_id)}
                className="rounded-lg border border-border bg-card p-3 text-left transition hover:border-primary/50"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="size-2 rounded-full"
                    style={{ background: colorForLabel(label) }}
                  />
                  <span
                    className="font-mono text-[9px] uppercase tracking-widest"
                    style={{ color: colorForLabel(label) }}
                  >
                    {label}
                  </span>
                </div>
                <div className="mt-1 truncate text-sm">{n.name}</div>
                <div className="truncate font-mono text-[10px] text-muted-foreground">
                  {n.node_id}
                </div>
              </button>
            );
          })}
          {!filtered.length && (
            <div className="col-span-full rounded-lg border border-dashed border-border p-10 text-center font-mono text-xs text-muted-foreground">
              No entities match this filter.
            </div>
          )}
        </div>
      </div>

      <NodeInspector nodeId={selected} onClose={() => setSelected(null)} onSelect={setSelected} />
    </div>
  );
}
