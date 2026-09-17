# ⚡ watsonx.data on IBM Power — Client Engineering Demo Recipe

> **Demonstrating Open Lakehouse Federation, Real-Time Streaming Analytics, and the IBM Power Advantage (50% Licensing Savings via SMT4 ÷4 & Co-Location Performance).**

---

## 🎯 Executive Summary & Purpose

Enterprises face escalating data egress costs, cloud sprawl, and latency challenges when attempting to run modern Data & AI workloads on legacy x86 architectures or public cloud silos. 

This recipe demonstrates how **IBM watsonx.data** deployed on or co-located with **IBM Power (Power10/Power11)** provides a high-performance open lakehouse architecture that:
1. **Eliminates Data Movement:** In-place federation across Db2 for IBM i, Oracle on AIX, Db2 Warehouse, and object storage.
2. **Cuts Software Licensing by up to 50%:** Leverages Power's hardware multithreading (`vCPU ÷ 4 = VPC`) for containerized IBM Software Hub / Cloud Pak workloads.
3. **Accelerates Analytics Without Dedicated GPUs:** Leverages Matrix Math Accelerators (MMA) and native vector engines (Gluten/Presto C++) for Spark and AI pipelines.

---

## ⏱️ 15-Minute Presales Demo Flow

| Time | Phase | Focus | Key Screen / Artifact |
|---|---|---|---|
| **00:00 - 03:00** | **The Hook** | Business Challenge: Siloed core systems (ERP on IBM i, Oracle on AIX) & cloud data costs | Slide / Discovery discussion |
| **03:00 - 08:00** | **Live Ingestion & Stream** | Synthetic real-time event generation simulating edge / operational data | `event-generators/` (e.g., Telco, Retail) |
| **08:00 - 12:00** | **Open Lakehouse Querying** | Real-time SQL aggregations federating with mission-critical systems in-place | `queries/` (Presto / Iceberg federated SQL) |
| **12:00 - 15:00** | **The Power Advantage Close** | 50% licensing reduction proof (÷4 rule) + MMA acceleration + zero data egress | `power-advantage/licensing-calc.html` |

---

## 🏗️ Architecture Overview

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    Operational Data & Event Streams                    │
 │    [ Retail POS ]     [ Telco Metrics ]     [ Finance ]   [ Healthcare]│
 └──────────────────────────────────┬─────────────────────────────────────┘
                                    │ Real-time Stream / Batch
                                    ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │            IBM watsonx.data Open Lakehouse (Red Hat OpenShift)         │
 │  ┌───────────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
 │  │      Presto C++       │  │   Apache Spark   │  │   OpenSearch    │  │
 │  │ (Distributed Queries) │  │ (MMA Accelerated)│  │ (RAG & Vectors) │  │
 │  └───────────┬───────────┘  └────────┬─────────┘  └────────┬────────┘  │
 │              │                       │                     │           │
 │              └───────────────────────┼─────────────────────┘           │
 │                                      ▼                                 │
 │         Apache Iceberg Open Table Formats / In-Place Federation        │
 └──────────────────┬───────────────────┬───────────────────┬─────────────┘
                    │                   │                   │
                    ▼                   ▼                   ▼
          ┌───────────────────┐ ┌───────────────┐ ┌───────────────────┐
          │  Db2 on IBM i     │ │ Oracle on AIX │ │ S3 Object Storage │
          │ (Core Enterprise) │ │ (Legacy ERP)  │ │ (Apache Iceberg)  │
          └───────────────────┘ └───────────────┘ └───────────────────┘
```

---

## 📂 Repository Structure

- `event-generators/` — Parameterized streaming event generators for 4 enterprise verticals.
- `queries/` — SQL query libraries showcasing in-place joins across streaming data & enterprise databases.
- `setup/` — Table definitions (DDL) for Iceberg lakehouse tables and federated catalog definitions.
- `power-advantage/` — Interactive SMT4 licensing calculator, seller objection handlers, and hardware sizing reference.
- `docs/` — Step-by-step customisation guide and technical briefs.

---

## 🚀 Quick Start for Sellers

### 1. Prerequisites
- Python 3.9+ (`pip install -r event-generators/requirements.txt`)
- Modern web browser (for `licensing-calc.html`)

### 2. Run a Real-Time Stream (Example: Telco Network Telemetry)
```bash
python event-generators/telco-network-metrics.py --rate 10 --duration 60 --anomalies
```

### 3. Open the Interactive Licensing Calculator
Open `power-advantage/licensing-calc.html` directly in your browser to demonstrate the exact dollar savings between x86 and IBM Power for the customer's sized workload.
