 AtmoGraph

🚨 Supply Chain Ripple Effect Predictor

Turning disruption signals into explainable supply-chain risk.
AtmoGraph combines NLP + Knowledge Graphs + Graph Traversal + Graph Neural Networks to understand how a disruption at one point of a supply chain can ripple through connected entities.

<p align="center">










</p>

✨ What is AtmoGraph?

Modern supply chains are deeply interconnected. A disruption at a port, supplier, manufacturer, warehouse, or transportation route can create a chain reaction across multiple dependent entities.

AtmoGraph is designed to model this problem as a graph and estimate the ripple effect of disruptions.

Instead of looking at a disruption in isolation, AtmoGraph asks:

🚨 “If this entity is disrupted, which connected entities could be affected, and how severe could the impact become?”

🎯 Core Objective

Build an intelligent system that can:

📰 Understand disruption/news text

🧠 Extract important supply-chain entities

🚨 Identify disruption types and severity

🕸️ Map entities to a supply-chain knowledge graph

🔎 Traverse connected supply-chain dependencies

📈 Estimate risk propagation

🤖 Use Graph Neural Networks for learned risk prediction

📊 Visualize the complete ripple effect through an interactive dashboard

🧠 How AtmoGraph Works

                         📰 NEWS / EVENT
                              │
                              ▼
                    ┌───────────────────┐
                    │    🧠 NLP LAYER   │
                    │                   │
                    │  spaCy NER        │
                    │  Entity Extraction│
                    │  Disruption Rules │
                    │  Severity         │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 🔗 ENTITY          │
                    │    RESOLUTION     │
                    │                   │
                    │ Text Entity       │
                    │       ↓           │
                    │ Neo4j Entity      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 🕸️ NEO4J GRAPH    │
                    │                   │
                    │ Supply Chain      │
                    │ Knowledge Graph   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 🔎 GRAPH          │
                    │    TRAVERSAL     │
                    │                   │
                    │ Connected Nodes   │
                    │ Hop Distance      │
                    │ Dependencies      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 📉 RISK BASELINE  │
                    │                   │
                    │ Hop-based Risk    │
                    │ Propagation       │
                    └─────────┬─────────┘
                              │
                              ▼
              ┌────────────────────────────────┐
              │ 🤖 GRAPH NEURAL NETWORK (GNN) │
              │                                │
              │ GraphSAGE / GCN                │
              │ PyTorch Geometric              │
              └───────────────┬────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 🎯 RISK SCORE     │
                    │                   │
                    │ Node-level Risk   │
                    │ 0.0 ─────── 1.0   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ ⚡ FASTAPI        │
                    │      API         │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ 🎨 REACT          │
                    │    DASHBOARD      │
                    │                   │
                    │ Interactive Graph │
                    │ Risk Analytics    │
                    │ Timeline          │
                    └───────────────────┘

🔥 The Ripple Effect

Imagine:

“Rotterdam port strike causes major shipping delays.”

AtmoGraph processes the event like this:

🚨 PORT STRIKE
      │
      ▼
⚓ Rotterdam Port
      │
      ├──────────────► 🚢 Shipping Route
      │                       │
      │                       ▼
      │                 🏭 Manufacturer
      │                       │
      │                       ▼
      │                 🏢 Warehouse
      │                       │
      │                       ▼
      │                 📦 Supplier
      │
      └──────────────► 🏢 Connected Company

The system identifies the disrupted entity and follows the relationships in the graph to determine where the disruption can propagate.

🕸️ Supply-Chain Knowledge Graph

AtmoGraph represents the supply chain using nodes + relationships.

📍 Main Nodes

Node

Description

🏭 Supplier

Provides raw materials/components

🏗️ Manufacturer

Produces products

🏢 Warehouse

Stores inventory

⚓ Port

Handles logistics/shipping

🚢 ShippingRoute

Represents transportation routes

📦 Product

Product/component being transported

🏢 Company

Business organization

🌍 Country

Geographic location

🔗 Relationships

Supplier ──SUPPLIES_TO──────► Manufacturer
Manufacturer ──MANUFACTURES─► Product
Company ──DEPENDS_ON────────► Supplier
Shipment ──SHIPS_THROUGH────► Port
Entity ──LOCATED_IN─────────► Country
Entity ──CONNECTED_TO───────► Entity

Supported relationship types:

SUPPLIES_TO

MANUFACTURES

SHIPS_THROUGH

LOCATED_IN

DEPENDS_ON

CONNECTED_TO

🧠 NLP Intelligence

The NLP layer converts unstructured text into structured disruption information.

Example

Input
│
└── "Rotterdam port strike causes major shipping delays."
             │
             ▼
      🧠 NLP Processing
             │
             ├── 📍 Entity → Rotterdam
             ├── 🚨 Type → PORT_STRIKE
             ├── ⚠️ Severity → High
             └── 🎯 Confidence → Model/rule confidence

NLP Components

🧠 spaCy Named Entity Recognition

🏷️ Supply-chain entity gazetteer

🚨 Rule-based disruption classification

🔗 Entity resolution against Neo4j

📊 Severity and confidence representation

🔎 Graph Traversal

Graph traversal means moving through connected nodes and relationships to discover the entities reachable from a disrupted node.

For example:

⚓ Port
   │
   ▼
🚢 Shipping Route
   │
   ▼
🏢 Warehouse
   │
   ▼
🏭 Manufacturer
   │
   ▼
📦 Supplier

The number of relationship steps is called the hop distance.

📉 Current Baseline

Hop

Baseline Risk

0

🔴 1.00

1

🟠 0.80

2

🟡 0.60

3

🟢 0.40

Note: This hop-decay approach is a baseline. The planned GNN will learn more complex graph-based patterns instead of relying only on fixed hop values.

🤖 Graph Neural Network

The next intelligence layer is a Graph Neural Network (GNN).

Traditional ML treats records mostly as independent samples. A GNN is designed for connected graph data, allowing the model to learn from:

🧩 Node features

🔗 Edge relationships

👥 Neighbor information

🕸️ Overall graph structure

Planned Models

GraphSAGE

GCN

PyTorch Geometric

🎯 Prediction

The target is a node-level:

risk_score ∈ [0, 1]

representing the predicted risk of disruption for each relevant supply-chain entity.

If historical labeled disruption data is unavailable, the initial prototype may use clearly documented synthetic disruption scenarios for model development and testing.

⚡ Backend

The backend is built with FastAPI and provides the service layer connecting NLP, Neo4j, risk analysis and future ML prediction.

🛠️ Backend Components

backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_graph.py
│   │   ├── routes_nlp.py
│   │   ├── routes_disruption.py
│   │   └── routes_prediction.py
│   │
│   ├── graph/
│   │   ├── neo4j_client.py
│   │   ├── queries.py
│   │   └── graph_service.py
│   │
│   ├── nlp/
│   │   ├── entity_extractor.py
│   │   ├── disruption_detector.py
│   │   └── pipeline.py
│   │
│   ├── services/
│   │   └── disruption_service.py
│   │
│   └── models/
│       └── schemas.py
│
├── data/
│   └── sample_supply_chain.json
│
├── scripts/
│   └── seed_neo4j.py
│
└── tests/

🔌 API

Method

Endpoint

Purpose

GET

/

API information

GET

/health

Backend health check

GET

/graph

Retrieve graph snapshot

GET

/graph/node/{node_id}

Retrieve a graph node

POST

/nlp/analyze

Analyze disruption text

POST

/disruption/analyze

Full disruption analysis

POST

/predict

GNN prediction endpoint

GET

/risk/nodes

Retrieve risk information

GET

/risk/timeline

Retrieve risk timeline

📚 API Documentation

FastAPI automatically provides interactive API documentation:

http://127.0.0.1:8000/docs

🏗️ Technology Stack

Layer

Technology

Purpose

🐍 Language

Python 3.10

Backend & ML

⚡ API

FastAPI

REST API

🚀 Server

Uvicorn

ASGI server

🧠 NLP

spaCy

Entity extraction

🕸️ Graph DB

Neo4j

Supply-chain graph

🔎 Query

Cypher

Graph querying

🤖 ML

PyTorch

Deep learning

🧩 GNN

PyTorch Geometric

Graph learning

🎨 Frontend

React

Dashboard

📘 Language

TypeScript

Frontend development

🕸️ Visualization

React Flow

Interactive graph

🧪 Testing

pytest

Automated testing

📂 Project Structure

Atmograph/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── graph/
│   │   ├── nlp/
│   │   ├── models/
│   │   ├── services/
│   │   ├── main.py
│   │   └── config.py
│   │
│   ├── data/
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── frontend/              # 🚧 Planned
    ├── src/
    ├── components/
    ├── pages/
    └── ...

📊 Current Capabilities

✅ Implemented

⚡ FastAPI backend

🔌 API routing

⚙️ Environment configuration

🕸️ Neo4j integration layer

🗃️ Synthetic supply-chain graph data

🧠 spaCy NLP pipeline

🚨 Disruption classification

🔗 Entity resolution logic

🔎 Graph traversal service

📉 Baseline risk propagation

🧪 Unit and mocked end-to-end tests

📚 API documentation through Swagger

🚧 In Development / Planned

🤖 GNN model training

📈 ML-based risk prediction

🧮 Graph feature engineering

🎨 React dashboard

🕸️ Interactive graph visualization

📊 Risk analytics and timeline

🔄 Complete frontend-backend integration

🧪 End-to-end production testing

🗺️ Roadmap

                         AT M O G R A P H
                              │
                              ▼
                 ┌──────────────────────┐
                 │ 🔬 Research & Design │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ ⚡ Backend Foundation│
                 │       ✅ DONE        │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ 🕸️ Neo4j + NLP      │
                 │    Verification      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ 🤖 GNN / ML         │
                 │ GraphSAGE / GCN     │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ 🎨 React Dashboard  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ 🔗 Full Integration │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ 🚀 Final Testing    │
                 │ & Demonstration     │
                 └──────────────────────┘

🎯 Final Vision

The final AtmoGraph experience should allow a user to enter a disruption and immediately understand its potential supply-chain ripple effect.

👤 USER
   │
   │  "Rotterdam port strike..."
   ▼
🧠 NLP
   │
   ▼
🚨 DISRUPTION DETECTED
   │
   ▼
⚓ AFFECTED PORT
   │
   ▼
🕸️ SUPPLY-CHAIN GRAPH
   │
   ├── 🚢 Routes
   ├── 🏢 Warehouses
   ├── 🏭 Manufacturers
   ├── 📦 Suppliers
   └── 🏢 Companies
   │
   ▼
🤖 GNN
   │
   ▼
📊 RISK PREDICTION
   │
   ▼
🎨 INTERACTIVE DASHBOARD

💡 Why AtmoGraph?

Traditional approach

🚨 Disruption
     ↓
❓ Manual investigation
     ↓
🐌 Slow analysis

AtmoGraph

🚨 Disruption
     ↓
🧠 NLP
     ↓
🕸️ Graph Intelligence
     ↓
🔎 Dependency Traversal
     ↓
🤖 GNN Prediction
     ↓
📊 Explainable Risk Visualization

🧪 Example Use Cases

⚓ Port strikes → identify affected routes and downstream businesses

🚢 Shipping delays → estimate impact on warehouses/manufacturers

🏭 Factory shutdowns → trace dependent suppliers and companies

📦 Supplier disruption → identify dependent manufacturers

🌪️ Natural disasters → analyze geographically connected supply-chain risks

🔐 Cyber incidents → model disruption to connected operational entities

🌍 Geopolitical events → investigate potential network-wide impact

🔐 Important Note

The current graph data is synthetic prototype data intended for development and demonstration.

The current hop-based risk propagation is a baseline. It should not be presented as a trained ML prediction model.

The GNN stage is intended to replace/augment this baseline with learned graph-based risk prediction.

👩‍💻 Project

AtmoGraph – Supply Chain Ripple Effect Predictor

Built around the idea of combining:

🧠 Natural Language Processing

🕸️ Knowledge Graphs

🔎 Graph Traversal

🤖 Graph Neural Networks

📊 Interactive Visualization

<p align="center">

🚨 From disruption detection to ripple-effect prediction.

AtmoGraph — See the chain reaction before it spreads. 🌐

</p>
