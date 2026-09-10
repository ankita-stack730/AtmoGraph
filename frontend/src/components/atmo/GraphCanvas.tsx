import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";
import type { GraphResponse } from "@/api/types";
import { colorForLabel, labelOf, riskBand, RISK_HEX } from "@/lib/risk";

const COLUMN_ORDER = [
  "Country",
  "Port",
  "ShippingRoute",
  "Supplier",
  "Manufacturer",
  "Product",
  "Warehouse",
  "Company",
];

type SupplyNodeData = {
  name: string;
  label: string;
  nodeId: string;
  risk: number | null;
  isSource: boolean;
  dimmed: boolean;
};

function SupplyNode({ data }: NodeProps) {
  const d = data as unknown as SupplyNodeData;
  const accent = colorForLabel(d.label);
  const risk = d.risk;
  const halo = risk === null ? null : RISK_HEX[riskBand(risk)];

  return (
    <div
      className="rounded-md border px-3 py-2 transition-opacity"
      style={{
        minWidth: 168,
        background: "#11151c",
        borderColor: halo ?? "rgba(148,163,184,0.28)",
        opacity: d.dimmed ? 0.28 : 1,
        boxShadow: halo
          ? `0 0 0 1px ${halo}55, 0 0 18px ${halo}55`
          : "0 1px 0 rgba(255,255,255,0.03)",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: accent, width: 6, height: 6 }} />
      <div className="flex items-center gap-2">
        <span className="size-2 rounded-full" style={{ background: accent }} />
        <span
          className="font-mono text-[9px] uppercase tracking-widest"
          style={{ color: accent }}
        >
          {d.label}
        </span>
        {d.isSource && (
          <span className="ml-auto rounded bg-white/10 px-1 font-mono text-[9px] uppercase text-white/80">
            src
          </span>
        )}
      </div>
      <div className="mt-1 max-w-[190px] truncate text-[12px] font-medium text-slate-100">
        {d.name}
      </div>
      <div className="mt-0.5 flex items-center justify-between font-mono text-[9px] text-slate-500">
        <span className="truncate">{d.nodeId}</span>
        {risk !== null && <span style={{ color: halo ?? undefined }}>{risk.toFixed(2)}</span>}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: accent, width: 6, height: 6 }} />
    </div>
  );
}

const nodeTypes = { supply: SupplyNode };

export interface GraphCanvasProps {
  graph: GraphResponse;
  riskById?: Record<string, number>;
  sourceIds?: string[];
  visibleLabels?: string[];
  highlightOnly?: boolean;
  onSelect?: (nodeId: string) => void;
}

export function GraphCanvas({
  graph,
  riskById = {},
  sourceIds = [],
  visibleLabels,
  highlightOnly = false,
  onSelect,
}: GraphCanvasProps) {
  const { nodes, edges } = useMemo(() => {
    const counters = new Map<string, number>();
    const included = graph.nodes.filter(
      (n) => !visibleLabels || visibleLabels.includes(labelOf(n.labels as string[])),
    );
    const includedIds = new Set(included.map((n) => n.node_id));

    const rfNodes: Node[] = included.map((n) => {
      const label = labelOf(n.labels as string[]);
      const col = Math.max(0, COLUMN_ORDER.indexOf(label));
      const idx = counters.get(label) ?? 0;
      counters.set(label, idx + 1);
      const risk = riskById[n.node_id];
      return {
        id: n.node_id,
        type: "supply",
        position: { x: col * 280, y: idx * 108 + (col % 2 === 0 ? 0 : 40) },
        data: {
          name: n.name,
          label,
          nodeId: n.node_id,
          risk: risk ?? null,
          isSource: sourceIds.includes(n.node_id),
          dimmed: highlightOnly && risk === undefined,
        } satisfies SupplyNodeData as unknown as Record<string, unknown>,
      };
    });

    const rfEdges: Edge[] = graph.relationships
      .filter((r) => includedIds.has(r.source) && includedIds.has(r.target))
      .map((r, i) => {
        const hot = riskById[r.source] !== undefined && riskById[r.target] !== undefined;
        return {
          id: `e${i}-${r.source}-${r.target}`,
          source: r.source,
          target: r.target,
          label: r.type,
          animated: hot,
          style: {
            stroke: hot ? "#00f0ff" : "rgba(148,163,184,0.28)",
            strokeWidth: hot ? 1.6 : 1,
          },
          labelStyle: { fill: "#64748b", fontSize: 8, fontFamily: "monospace" },
          labelBgStyle: { fill: "#0a0d12" },
        };
      });

    return { nodes: rfNodes, edges: rfEdges };
  }, [graph, riskById, sourceIds, visibleLabels, highlightOnly]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.15}
      proOptions={{ hideAttribution: true }}
      onNodeClick={(_, node) => onSelect?.(node.id)}
      className="bg-[#0a0d12]"
    >
      <Background color="#1e293b" gap={26} />
      <Controls className="!border !border-border !bg-card" />
      <MiniMap
        pannable
        zoomable
        maskColor="rgba(10,13,18,0.8)"
        style={{ background: "#11151c", border: "1px solid #1e293b" }}
        nodeColor={(n) => {
          const d = n.data as unknown as SupplyNodeData;
          return d.risk !== null ? RISK_HEX[riskBand(d.risk)] : colorForLabel(d.label);
        }}
      />
    </ReactFlow>
  );
}

export default GraphCanvas;
