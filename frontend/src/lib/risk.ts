export type RiskBand = "low" | "medium" | "high" | "critical";

export function riskBand(score: number): RiskBand {
  if (score >= 0.85) return "critical";
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

export const RISK_HEX: Record<RiskBand, string> = {
  low: "#22c55e",
  medium: "#f59e0b",
  high: "#fb7185",
  critical: "#ef4444",
};

export const RISK_TEXT: Record<RiskBand, string> = {
  low: "text-risk-low",
  medium: "text-risk-medium",
  high: "text-risk-high",
  critical: "text-risk-critical",
};

export const RISK_BADGE: Record<RiskBand, string> = {
  low: "border-risk-low/40 bg-risk-low/10 text-risk-low",
  medium: "border-risk-medium/40 bg-risk-medium/10 text-risk-medium",
  high: "border-risk-high/40 bg-risk-high/10 text-risk-high",
  critical: "border-risk-critical/40 bg-risk-critical/10 text-risk-critical",
};

export function severityBand(severity: string): RiskBand {
  const s = severity.toLowerCase();
  if (s === "critical") return "critical";
  if (s === "high") return "high";
  if (s === "medium" || s === "moderate") return "medium";
  return "low";
}

export const LABEL_COLOR: Record<string, string> = {
  Port: "#00f0ff",
  Supplier: "#a78bfa",
  Manufacturer: "#38bdf8",
  Warehouse: "#facc15",
  Product: "#34d399",
  Company: "#f472b6",
  Country: "#94a3b8",
  ShippingRoute: "#fb923c",
};

export function labelOf(labels: string[] | undefined): string {
  return labels?.[0] ?? "Unknown";
}

export function colorForLabel(label: string): string {
  return LABEL_COLOR[label] ?? "#7dd3fc";
}
