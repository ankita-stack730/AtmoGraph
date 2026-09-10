import type {
  NlpEntity,
  DisruptionResponse,
  GraphResponse,
  HealthResponse,
  NlpAnalyzeResponse,
  NodeDetail,
} from "./types";

type Raw = [string, string, string, Record<string, string | number>];

const RAW: Raw[] = [
  ["port_rotterdam", "Port of Rotterdam", "Port", { country: "Netherlands", teu_capacity: 14500000, criticality: "critical" }],
  ["port_shanghai", "Port of Shanghai", "Port", { country: "China", teu_capacity: 47000000, criticality: "critical" }],
  ["port_singapore", "Port of Singapore", "Port", { country: "Singapore", teu_capacity: 37200000, criticality: "high" }],
  ["port_hamburg", "Port of Hamburg", "Port", { country: "Germany", teu_capacity: 8300000, criticality: "high" }],
  ["port_la", "Port of Los Angeles", "Port", { country: "United States", teu_capacity: 9900000, criticality: "high" }],
  ["route_asia_eu", "Asia–Europe Trunk Route", "ShippingRoute", { transit_days: 32, mode: "sea" }],
  ["route_transpacific", "Transpacific Route", "ShippingRoute", { transit_days: 18, mode: "sea" }],
  ["route_north_sea", "North Sea Feeder", "ShippingRoute", { transit_days: 3, mode: "sea" }],
  ["sup_delta_semi", "Delta Semiconductor Works", "Supplier", { tier: 1, lead_time_days: 46 }],
  ["sup_nordic_steel", "Nordic Steel AB", "Supplier", { tier: 2, lead_time_days: 21 }],
  ["sup_pacific_poly", "Pacific Polymers Ltd", "Supplier", { tier: 2, lead_time_days: 27 }],
  ["sup_rhine_optics", "Rhine Optics GmbH", "Supplier", { tier: 1, lead_time_days: 34 }],
  ["sup_kyoto_cells", "Kyoto Cell Industries", "Supplier", { tier: 1, lead_time_days: 40 }],
  ["mfg_eindhoven", "Eindhoven Assembly Plant", "Manufacturer", { capacity_units_day: 12400, utilisation: 0.87 }],
  ["mfg_shenzhen", "Shenzhen Module Fab", "Manufacturer", { capacity_units_day: 38000, utilisation: 0.93 }],
  ["mfg_monterrey", "Monterrey Final Assembly", "Manufacturer", { capacity_units_day: 9100, utilisation: 0.71 }],
  ["wh_venlo", "Venlo Distribution Center", "Warehouse", { pallets: 42000, fill_rate: 0.78 }],
  ["wh_memphis", "Memphis Hub", "Warehouse", { pallets: 61000, fill_rate: 0.64 }],
  ["wh_felixstowe", "Felixstowe Bonded Store", "Warehouse", { pallets: 18500, fill_rate: 0.82 }],
  ["prod_ev_battery", "EV Battery Pack B9", "Product", { sku: "EVB-B9", margin_pct: 18 }],
  ["prod_sensor_array", "LiDAR Sensor Array", "Product", { sku: "LSA-220", margin_pct: 34 }],
  ["prod_control_unit", "Powertrain Control Unit", "Product", { sku: "PCU-77", margin_pct: 26 }],
  ["prod_display", "Automotive Display 12in", "Product", { sku: "AD-12", margin_pct: 22 }],
  ["co_veltron", "Veltron Mobility NV", "Company", { revenue_bn: 42.6, hq: "Amsterdam" }],
  ["co_arcadia", "Arcadia Motors Inc", "Company", { revenue_bn: 61.2, hq: "Detroit" }],
  ["co_hanwa", "Hanwa Electronics", "Company", { revenue_bn: 18.9, hq: "Osaka" }],
  ["ctry_nl", "Netherlands", "Country", { region: "EU", risk_index: 12 }],
  ["ctry_cn", "China", "Country", { region: "APAC", risk_index: 38 }],
  ["ctry_de", "Germany", "Country", { region: "EU", risk_index: 15 }],
  ["ctry_us", "United States", "Country", { region: "AMER", risk_index: 19 }],
];

const EDGES: [string, string, string][] = [
  ["port_rotterdam", "route_asia_eu", "SERVES_ROUTE"],
  ["port_shanghai", "route_asia_eu", "SERVES_ROUTE"],
  ["port_singapore", "route_asia_eu", "SERVES_ROUTE"],
  ["port_shanghai", "route_transpacific", "SERVES_ROUTE"],
  ["port_la", "route_transpacific", "SERVES_ROUTE"],
  ["port_rotterdam", "route_north_sea", "SERVES_ROUTE"],
  ["port_hamburg", "route_north_sea", "SERVES_ROUTE"],
  ["port_rotterdam", "ctry_nl", "LOCATED_IN"],
  ["port_hamburg", "ctry_de", "LOCATED_IN"],
  ["port_shanghai", "ctry_cn", "LOCATED_IN"],
  ["port_la", "ctry_us", "LOCATED_IN"],
  ["sup_delta_semi", "port_rotterdam", "SHIPS_THROUGH"],
  ["sup_rhine_optics", "port_rotterdam", "SHIPS_THROUGH"],
  ["sup_nordic_steel", "port_hamburg", "SHIPS_THROUGH"],
  ["sup_pacific_poly", "port_shanghai", "SHIPS_THROUGH"],
  ["sup_kyoto_cells", "port_singapore", "SHIPS_THROUGH"],
  ["sup_delta_semi", "mfg_eindhoven", "SUPPLIES"],
  ["sup_rhine_optics", "mfg_eindhoven", "SUPPLIES"],
  ["sup_nordic_steel", "mfg_eindhoven", "SUPPLIES"],
  ["sup_pacific_poly", "mfg_shenzhen", "SUPPLIES"],
  ["sup_kyoto_cells", "mfg_shenzhen", "SUPPLIES"],
  ["sup_pacific_poly", "mfg_monterrey", "SUPPLIES"],
  ["mfg_eindhoven", "prod_control_unit", "PRODUCES"],
  ["mfg_eindhoven", "prod_sensor_array", "PRODUCES"],
  ["mfg_shenzhen", "prod_display", "PRODUCES"],
  ["mfg_shenzhen", "prod_ev_battery", "PRODUCES"],
  ["mfg_monterrey", "prod_ev_battery", "PRODUCES"],
  ["prod_control_unit", "wh_venlo", "STORED_AT"],
  ["prod_sensor_array", "wh_venlo", "STORED_AT"],
  ["prod_display", "wh_felixstowe", "STORED_AT"],
  ["prod_ev_battery", "wh_memphis", "STORED_AT"],
  ["wh_venlo", "co_veltron", "DELIVERS_TO"],
  ["wh_felixstowe", "co_veltron", "DELIVERS_TO"],
  ["wh_memphis", "co_arcadia", "DELIVERS_TO"],
  ["prod_display", "co_hanwa", "DELIVERS_TO"],
  ["co_veltron", "ctry_nl", "HEADQUARTERED_IN"],
  ["co_arcadia", "ctry_us", "HEADQUARTERED_IN"],
  ["mfg_eindhoven", "ctry_nl", "LOCATED_IN"],
  ["mfg_shenzhen", "ctry_cn", "LOCATED_IN"],
];

export const MOCK_GRAPH: GraphResponse = {
  nodes: RAW.map(([node_id, name, label, properties]) => ({
    node_id,
    name,
    labels: [label],
    properties,
  })),
  relationships: EDGES.map(([source, target, type]) => ({ source, target, type })),
};

const NODE_BY_ID = new Map(RAW.map((r) => [r[0], r]));

export function mockNodeDetail(nodeId: string): NodeDetail {
  const raw = NODE_BY_ID.get(nodeId);
  if (!raw) {
    return { node_id: nodeId, name: nodeId, labels: ["Unknown"], properties: {} };
  }
  const rels = MOCK_GRAPH.relationships
    .filter((r) => r.source === nodeId || r.target === nodeId)
    .map((r) => {
      const otherId = r.source === nodeId ? r.target : r.source;
      return {
        type: r.type,
        direction: (r.source === nodeId ? "out" : "in") as "in" | "out",
        node_id: otherId,
        name: NODE_BY_ID.get(otherId)?.[1] ?? otherId,
      };
    });
  return {
    node_id: raw[0],
    name: raw[1],
    labels: [raw[2]],
    properties: raw[3],
    relationships: rels,
  };
}

export const MOCK_HEALTH: HealthResponse = {
  status: "demo",
  neo4j: "offline",
  nlp: "offline",
  gnn: "not_connected",
  version: "demo-baseline",
};

const ADJ = new Map<string, string[]>();
for (const [s, t] of EDGES) {
  ADJ.set(s, [...(ADJ.get(s) ?? []), t]);
  ADJ.set(t, [...(ADJ.get(t) ?? []), s]);
}

const KEYWORDS: { match: string[]; nodeId: string; type: string }[] = [
  { match: ["rotterdam"], nodeId: "port_rotterdam", type: "PORT" },
  { match: ["shanghai"], nodeId: "port_shanghai", type: "PORT" },
  { match: ["singapore"], nodeId: "port_singapore", type: "PORT" },
  { match: ["hamburg"], nodeId: "port_hamburg", type: "PORT" },
  { match: ["los angeles", "la port"], nodeId: "port_la", type: "PORT" },
  { match: ["eindhoven"], nodeId: "mfg_eindhoven", type: "FACILITY" },
  { match: ["shenzhen"], nodeId: "mfg_shenzhen", type: "FACILITY" },
  { match: ["monterrey"], nodeId: "mfg_monterrey", type: "FACILITY" },
  { match: ["netherlands"], nodeId: "ctry_nl", type: "COUNTRY" },
  { match: ["china"], nodeId: "ctry_cn", type: "COUNTRY" },
  { match: ["germany"], nodeId: "ctry_de", type: "COUNTRY" },
];

const EVENT_TYPES: { match: string[]; type: string; severity: string }[] = [
  { match: ["strike", "labor", "walkout"], type: "LABOR_STRIKE", severity: "high" },
  { match: ["typhoon", "hurricane", "storm", "flood", "earthquake"], type: "NATURAL_DISASTER", severity: "critical" },
  { match: ["cyber", "ransomware", "hack"], type: "CYBER_INCIDENT", severity: "high" },
  { match: ["tariff", "sanction", "embargo"], type: "TRADE_POLICY", severity: "medium" },
  { match: ["congestion", "delay", "backlog"], type: "CONGESTION", severity: "medium" },
  { match: ["fire", "explosion", "shutdown", "closure"], type: "FACILITY_OUTAGE", severity: "critical" },
];

export function mockNlp(text: string): NlpAnalyzeResponse {
  const lower = text.toLowerCase();
  const entities: NlpEntity[] = KEYWORDS.filter((k) => k.match.some((m) => lower.includes(m))).map((k) => ({
    text: NODE_BY_ID.get(k.nodeId)?.[1] ?? k.nodeId,
    type: k.type,
    matched_node_id: k.nodeId,
  }));
  const ev = EVENT_TYPES.find((e) => e.match.some((m) => lower.includes(m)));
  if (lower.includes("delay") && !entities.some((e) => e.type === "IMPACT")) {
    entities.push({ text: "shipping delays", type: "IMPACT", matched_node_id: null });
  }
  return {
    entities,
    event: { type: ev?.type ?? "UNCLASSIFIED", severity: ev?.severity ?? "low" },
  };
}

const SEVERITY_WEIGHT: Record<string, number> = {
  critical: 1,
  high: 0.86,
  medium: 0.62,
  low: 0.4,
};

export function mockDisruption(text: string): DisruptionResponse {
  const nlp = mockNlp(text);
  const sources = nlp.entities
    .map((e) => e.matched_node_id)
    .filter((v): v is string => Boolean(v));
  const seeds = sources.length ? sources : ["port_rotterdam"];
  const base = SEVERITY_WEIGHT[nlp.event.severity] ?? 0.5;

  const dist = new Map<string, number>();
  let frontier = [...new Set(seeds)];
  frontier.forEach((id) => dist.set(id, 0));
  let hop = 0;
  while (frontier.length && hop < 4) {
    hop += 1;
    const next: string[] = [];
    for (const id of frontier) {
      for (const nb of ADJ.get(id) ?? []) {
        if (!dist.has(nb)) {
          dist.set(nb, hop);
          next.push(nb);
        }
      }
    }
    frontier = next;
  }

  const nodes = [...dist.entries()]
    .map(([node_id, hop_distance]) => {
      const raw = NODE_BY_ID.get(node_id);
      const decay = Math.max(0, 1 - hop_distance * 0.27);
      const score = Math.round(base * decay * 100) / 100;
      return {
        node_id,
        name: raw?.[1] ?? node_id,
        labels: [raw?.[2] ?? "Unknown"],
        hop_distance,
        risk_score: score,
        is_source: hop_distance === 0,
      };
    })
    .sort((a, b) => b.risk_score - a.risk_score || a.name.localeCompare(b.name));

  return {
    event: nlp.event,
    entities: nlp.entities,
    matched_source_nodes: [...new Set(seeds)],
    affected_nodes: nodes.length,
    high_risk_nodes: nodes.filter((n) => n.risk_score >= 0.7).length,
    nodes,
    predictions: [],
    method: "GRAPH_BASELINE",
  };
}
