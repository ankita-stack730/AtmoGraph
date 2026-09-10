import { useQuery } from "@tanstack/react-query";
import { X, Link2, Info } from "lucide-react";
import { api } from "@/api/client";
import { colorForLabel, labelOf } from "@/lib/risk";

export function NodeInspector({
  nodeId,
  onClose,
  onSelect,
}: {
  nodeId: string | null;
  onClose: () => void;
  onSelect?: (id: string) => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["node", nodeId],
    queryFn: () => api.node(nodeId as string),
    enabled: Boolean(nodeId),
  });

  if (!nodeId) return null;
  const detail = data?.data;
  const label = labelOf(detail?.labels);

  return (
    <div className="absolute inset-y-0 right-0 z-20 flex w-full max-w-sm flex-col border-l border-border bg-card/95 backdrop-blur">
      <div className="flex items-start justify-between border-b border-border px-4 py-3">
        <div className="min-w-0">
          <div
            className="font-mono text-[10px] uppercase tracking-widest"
            style={{ color: colorForLabel(label) }}
          >
            {label}
          </div>
          <div className="truncate text-sm font-semibold">{detail?.name ?? nodeId}</div>
          <div className="truncate font-mono text-[10px] text-muted-foreground">{nodeId}</div>
        </div>
        <button
          onClick={onClose}
          className="rounded border border-border p-1 text-muted-foreground hover:text-foreground"
          aria-label="Close inspector"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-4">
        {isLoading && (
          <div className="font-mono text-xs text-muted-foreground">Loading node record…</div>
        )}

        {data?.source === "demo" && (
          <div className="flex items-start gap-2 rounded-md border border-primary/30 bg-primary/5 p-2 font-mono text-[10px] text-primary">
            <Info className="mt-px size-3" />
            Baseline record — GET /graph/node/{nodeId} unreachable.
          </div>
        )}

        <section>
          <h4 className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Properties
          </h4>
          <dl className="divide-y divide-border rounded-md border border-border">
            {Object.entries(detail?.properties ?? {}).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between gap-3 px-3 py-2">
                <dt className="font-mono text-[11px] text-muted-foreground">{k}</dt>
                <dd className="truncate font-mono text-[11px] text-foreground">{String(v)}</dd>
              </div>
            ))}
            {!isLoading && !Object.keys(detail?.properties ?? {}).length && (
              <div className="px-3 py-2 font-mono text-[11px] text-muted-foreground">
                No properties returned.
              </div>
            )}
          </dl>
        </section>

        <section>
          <h4 className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Relationships
          </h4>
          <div className="space-y-1">
            {(detail?.relationships ?? []).map((r) => (
              <button
                key={`${r.type}-${r.node_id}-${r.direction}`}
                onClick={() => onSelect?.(r.node_id)}
                className="flex w-full items-center gap-2 rounded-md border border-border px-3 py-2 text-left hover:border-primary/50 hover:bg-primary/5"
              >
                <Link2 className="size-3 text-primary" />
                <span className="font-mono text-[10px] uppercase text-muted-foreground">
                  {r.direction === "out" ? "→" : "←"} {r.type}
                </span>
                <span className="ml-auto truncate text-[11px]">{r.name}</span>
              </button>
            ))}
            {!(detail?.relationships ?? []).length && !isLoading && (
              <div className="rounded-md border border-border px-3 py-2 font-mono text-[11px] text-muted-foreground">
                No linked nodes returned.
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
