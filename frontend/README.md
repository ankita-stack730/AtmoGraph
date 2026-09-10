# ATMOgraph Command

Build the complete frontend for ATMOgraph: Supply Chain Ripple Effect Intelligence ("See the ripple. Predict the impact.").

CRITICAL ARCHITECTURE:
- Built in React, Vite, TypeScript, Tailwind CSS, Lucide icons, and @xyflow/react (React Flow) for graph visualization.
- Centralized API client in src/api/client.ts using import.meta.env.VITE_API_BASE_URL with fallback/default to 'http://127.0.0.1:8000'. Provide realistic fallback demo mock data whenever the backend is offline/unreachable so the UI renders fully during preview, with clear system badges indicating whether it is connected to live FastAPI or running in Demo / Baseline Mode.
- Endpoints:
  1. GET /health -> system/backend availability
  2. GET /graph -> supply chain graph { nodes, relationships }
  3. GET /graph/node/{node_id} -> detailed node properties
  4. POST /nlp/analyze -> { text } -> entities and disruption classification
  5. POST /disruption/analyze -> { text } -> { event: { type, severity }, entities: [...], matched_source_nodes: [...], affected_nodes, high_risk_nodes, nodes: [{ node_id, name, labels, hop_distance, risk_score, is_source }], predictions: [], method: "GRAPH_BASELINE" }
- ML Status: Honest "GNN prediction engine not connected" state when predictions: []; do not invent fake confidence or GNN metrics.
- UI Design: Palantir-inspired dark operational intelligence command center, deep charcoal (#0a0d12 / #11151c), subtle borders, electric cyan accents (#00f0ff / #0ea5e9), semantic risk colors (green low, amber medium, red critical/high), monospace font for IDs and technical metrics.
- Views & Shell:
  1. Persistent AppShell with sidebar (Overview, Network, Disruptions, Predictions, Entities, System Status), bottom engine status dots (API, Neo4j, Env), top bar with global search and connection state.
  2. Overview: Hero command center, quick disruption analyze trigger, KPI metrics, network summary.
  3. Network Graph: React Flow canvas with custom nodes (Port, Supplier, Manufacturer, Warehouse, Product, Company, Country, ShippingRoute), risk halos, zoom/pan/controls, filters, floating legend, and interactive slide-over Node Inspector using GET /graph/node/{node_id}.
  4. Disruption Analysis: Text input with preset sample ("Rotterdam port strike causes major shipping delays."), multi-step pipeline visualization, disruption summary banner, NLP entity badges (text, type, matched_node_id), interactive risk propagation tree, and automatic graph focus/highlight.
  5. Predictions: Honest separation between Graph Baseline (Active) and GNN Engine (Not connected).
  6. Entities: Searchable, filterable directory categorized by entity type.
  7. System Status: Real-time telemetry panel for FastAPI, Neo4j, NLP, Graph Engine, GNN.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://atmo-flow.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/4d58e8d7-dc0f-4125-9e04-c8c93406cd3b).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
