export type NodeLabel =
  | "Port"
  | "Supplier"
  | "Manufacturer"
  | "Warehouse"
  | "Product"
  | "Company"
  | "Country"
  | "ShippingRoute";

export interface GraphNode {
  node_id: string;
  name: string;
  labels: NodeLabel[] | string[];
  properties?: Record<string, unknown>;
}

export interface GraphRelationship {
  source: string;
  target: string;
  type: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
}

export interface NodeDetail {
  node_id: string;
  name: string;
  labels: string[];
  properties: Record<string, string | number | boolean>;
  relationships?: { type: string; direction: "in" | "out"; node_id: string; name: string }[];
}

export interface NlpEntity {
  text: string;
  type: string;
  matched_node_id?: string | null;
}

export interface NlpAnalyzeResponse {
  entities: NlpEntity[];
  event: { type: string; severity: string };
}

export interface RippleNode {
  node_id: string;
  name: string;
  labels: string[];
  hop_distance: number;
  risk_score: number;
  is_source: boolean;
}

export interface DisruptionResponse {
  event: { type: string; severity: string };
  entities: NlpEntity[];
  matched_source_nodes: string[];
  affected_nodes: number;
  high_risk_nodes: number;
  nodes: RippleNode[];
  predictions: unknown[];
  method: string;
}

export interface HealthResponse {
  status: string;
  neo4j?: string;
  nlp?: string;
  gnn?: string;
  version?: string;
}
