# Story Briefs — Audience-Specific Presenter Scripts

> **Purpose:** Give the seller tailored opening/closing scripts for each audience persona so the demo lands without improvisation. Each brief includes the "production pipeline" explanation for that audience.
>
> **Demo Arc:** 4 pages — Static Map (`/`) → Architecture (`/sources`) → Live Satnav (`/live?scenario=cyber|wildfire`) → Outcome (`/outcome?scenario=cyber|wildfire`)
>
> **Metaphor:** "Road Atlas → Satnav" — static weekly reports (3 days old, false confidence) vs. live federated intelligence (real-time, actionable)

---

## Common Elements (All Audiences)

### The Core Punchlines (Memorise These)
| Moment | Line |
|--------|------|
| **Page 1 reveal** | *"This report isn't wrong — it's just 3 days old. In a static world, that's fine. In a world of zero-day exploits and climate-driven logistics disruption, it's dangerous."* |
| **Page 2 transition** | *"Your ERP knows your orders. Your operational DB knows the tier-2 graph. Your live stream knows the threats. They never talk to each other — until watsonx.data federates them. No ETL. No data movement. Single query, <2 seconds."* |
| **Page 3 injection** | *"Watch what happens when the signal arrives. The detector joins it to your supplier graph and live orders in under 2 seconds. This alert? `NOT VISIBLE IN ERP WITHOUT FEDERATION`."* |
| **Page 4 outcome** | *"Same event. Same data. The difference is entirely time to action — 80 hours vs 5 hours. £15K vs £1K. The data was always there. The gap wasn't information — it was time and joinability."* |

### Production Pipeline — One-Liner (Adapt per Audience)
> **Universal:** *"In production, this button click = continuous pipeline. CISA KEV polled every 5 minutes, route telemetry via webhooks, Kafka/Flink stream processor auto-triggers the **same federated query** and routes alerts to your SIEM/SOAR/ServiceNow/PagerDuty. The demo simplifies the trigger and the sink for narrative clarity — the federation layer is identical."*

---

## 🎯 Audience 1: CISO / Security Leader

**Time:** ~8 minutes total | **Tone:** Urgent, risk-focused, compliance-aware

### Opening Hook (30 sec)
> *"Hold up a physical road atlas — or mime it. 'This is your weekly security posture report. Printed Friday 6am. Today is Monday. Zero incidents flagged. All suppliers green.'* [pause] *'Your ERP has never heard of Nexaflow Logistics. They're a tier-2 subcontractor. The MOVEit breach (CVE-2023-34362) won't show up here until a tier-1 supplier calls to say they can't deliver. By then, £47k of exposure has already shipped. Let me show you what the atlas missed.'"*

### Page-by-Page Narration

| Page | Point Here | Say This |
|------|------------|----------|
| **1. Static Map** | Red "3 Days Old" banner | *"72 hours ago this map was accurate. In those 72 hours: a tier-2 supplier was compromised via a known exploited vulnerability, 14 open POs exposed, 6 tier-1 suppliers affected. None of it appears on this report."* |
| | KPI "Cyber Incidents: 0" | *"Zero — because your ERP has zero visibility of tier-2 suppliers. The breach lives in your operational DB and threat feed, not your ERP."* |
| | Supplier table footnote | *"'Tier-2 sub-contractors are not visible in ERP.' That's the blindspot. Nexaflow Logistics Ltd — COMPROMISED — 14 POs, £47k, 6 tier-1s affected. Invisible."* |
| **2. Architecture** | Source 1 (IBM i) blindspot | *"Your system of record. 99k orders, 32k products. Real Db2 for i on real Power. But it knows nothing of Nexaflow — that tier-2 lives in Source 2."* |
| | Source 2 (EDB) held data | *"50 subcontractors. The tier-2 graph. Nexaflow sits here with breach_status=COMPROMISED. But Source 2 has no link to live orders — it doesn't know which POs are at risk."* |
| | Source 3 (Iceberg) held data | *"Live CISA Known Exploited Vulnerabilities feed. The breach signal arrives HERE. But without corporate context, it's just noise — it doesn't know your POs use this supplier."* |
| | Satnav Engine banner | *"This is the detection engine. When a signal arrives in Source 3, the detector instantly joins it to Source 2 (who's affected?) and Source 1 (what's the exposure?). In production: continuous pipeline (CISA KEV polling 5-min, Kafka/Flink) auto-triggers this same federation → your SIEM."* |
| **3. Live Satnav** | "Inject Signal" button | *"This button = the production pipeline trigger. In production: CISA KEV API polled every 5 minutes, normalised into Kafka, Flink processor auto-triggers the same federated query on signal match."* |
| | Query executing spinner | *"Federated query: IBM i × EDB × Iceberg. <2 seconds. Zero ETL. Presto pushes predicates down to each source."* |
| | KEY PUNCHLINE block | ***Read it verbatim:*** **"NOT VISIBLE IN ERP WITHOUT FEDERATION"** — *"Your ERP has zero visibility of this tier-2 supplier. Federation is the only way to see this exposure."* |
| | Source badge: "live federation query" | *"Green badge = real query against your TechZone watsonx.data Dev Image. Not simulated."* |
| **4. Outcome** | Hero metrics: 80h → 5h | *"80 hours to detect in the old world. 5 hours with federation. That's the difference between a contained incident and a reportable breach."* |
| | Business actions | *"11 of 14 POs re-routed BEFORE the breach disrupted supply. 0 SLA breaches. £14K cost avoided."* |
| | Power pillar: Security | *"IBM i's object-based memory architecture neutralises buffer overflows and code injection — common exploit vectors simply don't work. PowerSC gives continuous compliance scoring built-in. Single vendor accountability."* |

### Closing & Objection Handling (30 sec)
> **Close:** *"The breach was always going to happen. The question is whether you find out in 5 hours or 80. watsonx.data on IBM Power gives you the satnav — continuous threat feed ingestion, auto-enrichment with your supplier graph, SIEM ticket in seconds. Not weeks."*

| Objection | Response |
|-----------|----------|
| *"We already have a SIEM"* | *"SIEM sees logs. It doesn't see your tier-2 supplier graph or live POs. This enriches your SIEM with business context — supplier → PO → customer → £ exposure."* |
| *"Our ERP has supplier risk modules"* | *"ERP modules see tier-1 only. They cannot join CISA KEV feeds to tier-2 subcontractors to open purchase orders across three systems in <2 seconds. That's federation, not a module."* |
| *"This looks like SaaS — where's my data?"* | *"watsonx.data runs on IBM Power — on-prem or your IBM Cloud tenant. Your data never leaves your environment. Federation queries in-place. Zero data movement."* |

---

## 🏗 Audience 2: Data Architect / Engineer

**Time:** ~10 minutes total | **Tone:** Technical, precise, architecture-focused

### Opening Hook (30 sec)
> *"This is a federated query engine running on RHEL on IBM Power. It joins Db2 for i on an LPAR, PostgreSQL on a Power VM, and Apache Iceberg on Cloud Object Storage — in under 2 seconds. Zero ETL. No data movement. No CDC pipelines to maintain. The 'road atlas' on Page 1? That's what happens when you rely on nightly ETL and materialised views. Let me show you the satnav."*

### Page-by-Page Narration

| Page | Point Here | Say This |
|------|------------|----------|
| **1. Static Map** | Stale timestamp | *"Report generated Friday 06:00. Viewed Monday 09:14. That's 72 hours of staleness. In data engineering terms: your materialised views are 3 days behind. Your CDC pipeline lag is 72 hours."* |
| | KPI blindspot badges | *"Each green KPI has a 'Blindspot' badge. Cyber Incidents: 0 — because the CISA KEV feed isn't in your warehouse. Freight Disruptions: 0 — because route telemetry isn't joined to your PO fact table."* |
| **2. Architecture** | Three source cards | *"Source 1: IBM i, Db2 for i, native Presto connector. Source 2: EDB Postgres, standard PostgreSQL connector. Source 3: Apache Iceberg on COS, Iceberg connector. Three connectors. One Presto engine. One SQL dialect."* |
| | Satnav Flow Diagram | *"External Signal → Iceberg → Federated Query → Internal Dependency Match → Alert. The federation layer is Presto. Predicate pushdown to each connector. <2s end-to-end."* |
| | "Production Pipeline" note | *"In production: Kafka topic for normalised signals → Flink/Kafka Streams processor → on new signal match, executes the **exact same Presto SQL** → writes results to Iceberg sink → SIEM/SOAR webhook. The demo button = the Flink trigger."* |
| **3. Live Satnav** | "How it Works" modal → Technical footnote | *"Read the footnote: 'Zero-ETL federated Presto query across IBM i (Db2 for i), PostgreSQL/EDB, and Apache Iceberg on Cloud Object Storage, executing in <2 seconds on RHEL on IBM Power.' The ingestion pipeline (Kafka/Flink on OpenShift) and response automation (ServiceNow/Ansible) are operational additions."* |
| | DataSourcePanel → Live Query tab | *"Click 'Live Query' tab. This is the actual SQL sent to watsonx.data. Notice: 3-way join across catalogs `ibmi_olist`, `pg_olist`, `retail_signals`. Presto plans this as a single distributed query."* |
| | Query executing spinner | *"Executing federated query across 3 sources... <2s. That's wall-clock time. Not a materialised view refresh. Not a CDC catch-up. Live."* |
| **4. Outcome** | Power pillar: MMA | *"Matrix Math Accelerator on Power10. On-box AI scoring — risk models, anomaly detection — without shipping data to a GPU cluster. No data egress. No separate ML infra. The same CPU cores running your ERP run the inference."* |
| | Power pillar: Hybrid | *"Same ISA (Power ISA), same operating model, same security posture — on-prem LPAR or IBM Cloud PowerVS. Workload mobility without re-platforming. Your Iceberg tables on COS are accessible from both."* |

### Closing & Objection Handling (30 sec)
> **Close:** *"The data was always there. The gap wasn't information — it was time and joinability. A static report cannot ask a question that spans three systems. watsonx.data on IBM Power can. In under 2 seconds. On hardware you already own."*

| Objection | Response |
|-----------|----------|
| *"Presto federation has latency"* | *"<2 seconds for a 3-way join across IBM i, Postgres, and Iceberg with predicate pushdown. That's not federation latency — that's network + planner. On Power10 with local Satellite tunnels, it's sub-second for cached metadata."* |
| *"We use Spark/Trino/Databricks"* | *"Trino is Presto's fork — same federation model. But watsonx.data adds: native IBM i connector, Iceberg on COS with time-travel, MMA acceleration, and unified governance. And it runs on the same Power hardware as your ERP."* |
| *"Iceberg on COS — vendor lock-in?"* | *"Apache Iceberg is 100% open. COS is S3-compatible. Your tables, your metadata, your catalog. watsonx.data is a managed Presto + Iceberg catalog service — you can run open-source Presto + Iceberg yourself if you want. The connector configs are portable."* |

---

## 📦 Audience 3: Supply-Chain / Procurement Leader

**Time:** ~7 minutes total | **Tone:** Operational, money-focused, action-oriented

### Opening Hook (30 sec)
> *"This is your Monday morning freight report. Printed Friday. Everything green — all routes clear, all suppliers active, all POs on track. *But the A9/AP-7 corridor closed Saturday. Three POs are stuck. Your report still says 'ON TRACK.'* Let me show you what happens when your freight data talks to your order data in real time."*

### Page-by-Page Narration

| Page | Point Here | Say This |
|------|------------|----------|
| **1. Static Map** | Freight POs table | *"Three POs on the A9/AP-7 corridor. Lyon → Barcelona, Lyon → Valencia, Paris → Madrid. All show 'ON TRACK.' The footnote: 'Route status based on Friday morning road network data. No real-time updates.'"* |
| | "What this table CANNOT see" | *"Real-time route conditions. Warehouse corridor mappings. Demand spikes from live POS. The wildfire that closed the A9/AP-7 isn't in this report — but it's in your route telemetry feed."* |
| **2. Architecture** | Source 2 (EDB) held data | *"This is where your warehouse corridor mappings live. South France, Catalonia, Mediterranean regions. The A9/AP-7 corridor is mapped here. But Source 2 has no link to live freight POs."* |
| | Source 3 (Iceberg) held data | *"Route & Travel Disruption Intelligence. Freight corridor sensor data. The wildfire closure signal arrives HERE. But it doesn't know your POs use this corridor — that context is in Source 1 + 2."* |
| | Satnav Engine banner | *"When the route disruption signal hits Iceberg, the detector joins it to warehouse corridors (Source 2) and active freight POs (Source 1). In production: route webhook → Kafka → Flink auto-triggers federation → PagerDuty alert to your on-call freight manager."* |
| **3. Live Satnav** | Inject "eu-wildfire" signal | *"This simulates the route disruption webhook arriving. Watch the detector pinpoint exactly which POs are at risk."* |
| | Wildfire alert card | *"5 of 7 POs at risk. Supplier regions: South France, Catalonia. Earliest ship limit: tomorrow. Total exposure: £X. The alert tells you WHAT to reroute, WHERE from, and BY WHEN."* |
| | "What this enables" | *"✓ 5 of 7 POs re-routed before business day starts. ✓ 0 stockouts — demand spike detected in real-time POS stream, inventory rebalanced. ✓ £6.8K cost avoided vs £8.7K in the static world."* |
| **4. Outcome** | Hero metrics: 96h → 1.5h | *"4 days to react in the old world. 90 minutes with the satnav. That's the difference between empty shelves and a normal Tuesday."* |
| | Business actions cards | *"Pre-approved rerouting via Alpine passes. On-call manager alerted at 06:02. POs redirected by 07:30. SLAs protected. Stockouts: zero."* |

### Closing & Objection Handling (30 sec)
> **Close:** *"The road was always going to close. The question is whether you act in 90 minutes or 4 days. watsonx.data on IBM Power gives your freight team the satnav — route feed webhook hits, warehouse corridor match, PagerDuty alert to on-call manager in seconds. Your POs are rerouted before the coffee's cold."*

| Objection | Response |
|-----------|----------|
| *"Our TMS has route optimisation"* | *"TMS optimises planned routes. It doesn't ingest live wildfire sensors, join to your warehouse corridor graph, and tell you which specific POs on which specific carriers are affected — in seconds. This is event-driven, not plan-driven."* |
| *"We get carrier alerts"* | *"Carrier alerts tell you THEIR delay. This tells you YOUR exposure — which POs, which customers, how much revenue at risk, which alternative corridors exist in YOUR network. Before the carrier calls."* |
| *"Too technical for my team"* | *"The detector runs automatically. Your team gets a PagerDuty/ServiceNow alert: 'PO-2017-00142 at risk — A9/AP-7 closed — suggested reroute via Alpine pass — approve?' One click. No SQL. No federation knowledge needed."* |

---

## 🎯 Audience 4: IT Director / C-Suite / Business Leader

**Time:** ~6 minutes total | **Tone:** Strategic, outcome-focused, vendor-agnostic language

### Opening Hook (30 sec)
> *"Your business runs on a weekly report. It's 3 days old. It says everything's fine. But in those 3 days: a critical supplier was breached, a key freight corridor closed, and £47k of exposure shipped unnoticed. The report isn't wrong — it's just obsolete the moment it's printed. Let me show you the alternative: live intelligence that turns 80-hour response into 5-hour response, and £15K incidents into £1K admin."*

### Page-by-Page Narration

| Page | Point Here | Say This |
|------|------------|----------|
| **1. Static Map** | "This Road Atlas Is 3 Days Old" banner | *"In 72 hours: tier-2 supplier compromised (MOVEit CVE), freight corridor closed (wildfire), 14 POs at risk, £47k exposure. None of it on this map. The atlas shows where you were. The satnav shows where you're heading."* |
| | KPI row — all green with "Blindspot" badges | *"Every green KPI has a red 'Blindspot' badge. Cyber: 0 — because ERP never hears of tier-2 breaches. Freight: 0 — because route data frozen Friday. Suppliers: 53 — counts tier-1 only. 50 tier-2s invisible."* |
| **2. Architecture** | Three sources diagram | *"Your ERP (IBM i) knows orders. Your operational DB (Postgres) knows the supplier graph. Your live stream (Iceberg) knows threats and road conditions. They never talk. watsonx.data makes them talk — one query, no ETL, <2 seconds."* |
| | "Satnav Engine" banner | *"In production: continuous pipeline auto-triggers this. CISA KEV polling, route webhooks, Kafka/Flink streaming. The demo button = the pipeline trigger. Same query. Same result."* |
| **3. Live Satnav** | Signal injection + alert | *"One click. Signal ingested. Federation runs. Alert fired. `NOT VISIBLE IN ERP WITHOUT FEDERATION` — that's the punchline. The data existed. The join didn't. Until now."* |
| | "What this enables" | *"Hold/re-route POs before they ship. Pre-qualify alternatives in seconds. Notify procurement with exact tier-2 names ERP never heard of."* |
| **4. Outcome** | Hero metrics row | *"80 hours → 5 hours. £15K → £1K. 16× faster. 0 SLA breaches. The data was always there. The gap was time and joinability."* |
| | Power pillars summary | *"IBM i runs your ERP. Power runs the intelligence. MMA = AI without GPU clusters. Hybrid = move workloads without re-platforming. Security = architecture-level, not bolt-on. One vendor: IBM owns the stack."*

### Closing & Objection Handling (30 sec)
> **Close:** *"IBM i runs your ERP. IBM Power runs the intelligence that watches over it. The breach was always going to happen. The road was always going to close. The question is whether you act in hours or days. watsonx.data on IBM Power gives you the satnav — managed ingestion pipeline on OpenShift, federation to your existing ERP, ServiceNow workflow for action. One vendor conversation. One throat to choke."*

| Objection | Response |
|-----------|----------|
| *"We're on Azure/AWS/GCP — why Power?"* | *"Your ERP (IBM i) already runs on Power. watsonx.data federates to it in-place — no migration. Run the intelligence layer on the same hardware as the data. Or run it on IBM Cloud PowerVS — same ISA, same model. Hybrid flexibility."* |
| *"This looks like another platform"* | *"It's a federation layer. It sits *above* your existing systems — IBM i, Postgres, Iceberg — and makes them queryable together. No rip-and-replace. No data migration. It unlocks what you already have."* |
| *"What's the TCO?"* | *"Compare: 72-hour incident response vs 5-hour. £15K avg incident cost vs £1K. 16-64× speedup. Eliminate nightly ETL pipelines. Consolidate GPU inference to on-box MMA. Single vendor support. The ROI is in avoided incidents, not infrastructure spend."* |

---

## Production Pipeline — Per-Audience Cheat Sheet

| Audience | Production Pipeline One-Liner |
|----------|-------------------------------|
| **CISO** | *"Continuous threat feed ingestion (CISA KEV polling 5-min) → auto-enrichment with your supplier graph → SIEM ticket (QRadar/Splunk) → SOAR playbook"* |
| **Data Architect** | *"Kafka/Flink stream processor → normalised signal topic → federated Presto query (IBM i × Postgres × Iceberg) → Iceberg sink → downstream consumers"* |
| **Supply-Chain** | *"Route feed webhook → warehouse corridor match → PagerDuty alert to on-call manager → pre-approved reroute workflow in ServiceNow"* |
| **IT Director** | *"Managed ingestion pipeline on OpenShift → watsonx.data federation → ServiceNow workflow → single vendor accountability (IBM owns ERP + hardware + lakehouse + security)"* |

---

## Quick Reference: Demo Navigation Flow

```
START:  http://129.40.125.69:3000/                    (Page 1: Static Map)
   ↓ "See the Live Satnav →"
NEXT:   http://129.40.125.69:3000/sources             (Page 2: Architecture)
   ↓ "Launch Live Satnav — Scenario 1 (Cyber)"
NEXT:   http://129.40.125.69:3000/live?scenario=cyber  (Page 3: Live Satnav - Cyber)
   ↓ "Inject Signal" → wait for alert → "See the outcome →"
NEXT:   http://129.40.125.69:3000/outcome?scenario=cyber (Page 4: Outcome - Cyber)
   ↓ "Run Scenario 2 — Wildfire →"
NEXT:   http://129.40.125.69:3000/live?scenario=wildfire (Page 3: Live Satnav - Wildfire)
   ↓ "Inject Signal" → wait for alert → "See the outcome →"
NEXT:   http://129.40.125.69:3000/outcome?scenario=wildfire (Page 4: Outcome - Wildfire)
   ↓ "Start again →"
END:    http://129.40.125.69:3000/                    (Back to Page 1)
```

---

## Speaker Notes Panels (Built Into Demo)

| Page | Toggle Location | Content |
|------|-----------------|---------|
| **Static Map** | Top-right "Speaker Notes" button | 5 sections: Opening, KPIs, Supplier Table, Freight Table, Closing |
| **Architecture** | Top-right "Speaker Notes" button | 5 sections: Why Three Sources, Source 1, Source 2, Source 3, Satnav Engine Reveal |
| **Live Satnav** | Top bar "How it works" button | Modal: Satnav analogy (3 steps), Demo vs Production table, Technical footnote |
| **Outcome** | Bottom "Next steps for your role ▸" accordion | 4 audience cards: CISO, Data Architect, Supply-Chain, IT Director |

---

## Key Metrics to Memorise

| Scenario | Old World | New World | Saving | Speedup |
|----------|-----------|-----------|--------|---------|
| **Cyber** | 80 hrs, £15.2K | 5 hrs, £1.2K | £14K (92%) | 16× |
| **Wildfire** | 96 hrs, £8.7K | 1.5 hrs, £1.9K | £6.8K (78%) | 64× |

**Key Entities:**
- **Nexaflow Logistics Ltd** — COMPROMISED tier-2 supplier (MOVEit CVE-2023-34362)
- **A9/AP-7 Corridor** — France/Spain freight route, wildfire closure
- **14 open POs** — £47,230 exposure, 6 tier-1 suppliers affected
- **3 POs on A9/AP-7** — at risk in wildfire scenario

---

## Environment Status (For Q&A)

| Component | Status | Details |
|-----------|--------|---------|
| **watsonx.data** | Dev Image 2.2.0 GA | VMware on TechZone `eu-de`, Presto `:46662`, Basic auth |
| **IBM i** | On-prem Power10 | `129.40.125.73:8471`, RDB `PVM02XJK`, via Satellite tunnel |
| **PostgreSQL/EDB** | RHEL on Power10 | `129.40.125.69:5432`, via Satellite tunnel |
| **Satellite** | Connector `wxd-power-connector` | Agent Up on RHEL, 4 endpoints active |
| **Demo UI** | `http://129.40.125.69:3000` | Next.js on RHEL, all routes HTTP 200 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-18 | Bob | Initial creation — 4 audience briefs with production pipeline per audience |