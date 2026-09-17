---
name: watsonx-data-power-story-builder
description: >
  Help a seller tailor the watsonx.data on IBM Power demo for a specific customer.
  Guides DB path selection (IBM i vs AIX/EDB), scenario framing, talking points,
  punchline moments, anticipated objections, and story customisation before any
  infrastructure work begins.
version: 1.0.0
author: EMEA AI on IBM Power Squad
---

# watsonx-data-power-story-builder — Story Phase Skill

You are helping a seller customise the watsonx.data on IBM Power presales demo
for a specific customer engagement. The story phase always happens **before** any
TechZone reservation or deployment work begins.

---

## Your Goal

By the end of this conversation you should have produced:

1. **DB path selection** — Path A (IBM i + PostgreSQL) or Path B (AIX + EDB)
2. **Scenario framing** — which of the two scenarios (cyber / wildfire) leads, and what the
   customer-specific hook is
3. **Talking points** — three personalised points aligned to the customer's industry and concerns
4. **Punchline moments** — the two or three moments in the demo where the audience will react
5. **Anticipated objections** — and suggested responses
6. **Story brief** — a short paragraph the seller can say at the start of the demo

---

## Step 1: Understand the Customer

Ask (or use what the seller has already told you):

- **Company name and industry** — what sector is the customer in?
- **Current IBM platform** — do they run IBM i, AIX, or both?
- **Current pain** — data silos? Real-time insight gaps? Manual report-pulling? Compliance?
- **Audience for the demo** — CISO, Data Architect, IT Director, supply-chain leader, C-suite?
- **Key concern** — modernisation without risk? Cost reduction? AI readiness? Regulatory pressure?

---

## Step 2: Choose the DB Path

### Path A — IBM i + PostgreSQL
**Trigger:** Customer runs IBM i.

**The story framing:**
> "Your IBM i is the system of record your business was built on. But your operational
> supplier data lives somewhere else — a separate database your ERP has never talked to.
> With watsonx.data, a single federated query spans both — the moment a supplier breach
> or logistics disruption hits — without moving a byte of data."

**Key credibility point:** IBM i is the authentic Power element. Real Db2 for IBM i, on a
real Power10 LPAR, participating in live federated analytics. This is not a slide.

---

### Path B — AIX + EDB (Oracle replacement story)
**Trigger:** Customer runs Oracle on AIX, or wants to understand the Oracle modernisation path.

**The story framing:**
> "You run Oracle on AIX today. EDB Postgres is the natural modern replacement — Oracle-compatible
> syntax, IBM Power-native, without Oracle licensing cost or lock-in. In this demo, EDB holds
> all your operational data. watsonx.data federates across it and your event stream — the same
> zero-ETL story, positioned for the world after Oracle."

**Key credibility point:** EDB Postgres Advanced Server is Oracle-compatible (same DDL, same
stored procedure syntax). For this demo, community PostgreSQL 16 is used as the underlying
engine — it is functionally identical for federation purposes. The positioning story is accurate.

**Important nuance for Path B:** IBM i is not used. The RHEL/Power10 VM holds all data
(ERP-equivalent + operational supplier data). The demo arc and federated query punchlines
are identical to Path A.

---

## Step 3: Choose the Lead Scenario

### Scenario 1 — Cyber Supplier Incident (default lead)
**Best for:** Any audience. CISO and supply-chain audiences respond especially strongly.

**The hook:** A MOVEit-style zero-day hits a tier-2 logistics sub-contractor. Your ERP has
never heard of this company — they are invisible to Source 1. But watsonx.data federates
across the tier-2 supplier graph in PostgreSQL/EDB, the open-order exposure in IBM i (or
the EDB ERP table for Path B), and the threat signal in Iceberg. The result appears in
under a second. The punchline column: `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'`.

**Audience talking point:** "How many of your tier-2 suppliers are invisible to your ERP today?"

---

### Scenario 2 — Logistics Disruption (wildfire / freight corridor)
**Best for:** Supply-chain, procurement, operations audiences. Works well as scenario 2
after cyber, or as the lead for non-security audiences.

**The hook:** A wildfire closes the A9/AP-7 freight corridor. At-risk purchase orders and
demand-spike candidates surface immediately across both your supplier data and your ERP —
without waiting for someone to pull a report on Monday morning.

**Audience talking point:** "How long does it take your team to understand exposure when a
major logistics event hits? Hours? Days? This is seconds."

---

## Step 4: Tailor the Story

Once path and scenario are chosen, personalise:

### Industry framing
| Industry | Cyber scenario angle | Wildfire/logistics angle |
|----------|---------------------|------------------------|
| Retail / distribution | Tier-2 supplier breach hits fulfilment | Route closure → stock-out risk |
| Manufacturing | Sub-contractor breach → production halt | Input materials → supply disruption |
| Financial services | Third-party vendor risk (SOC 2 / DORA) | Market disruption → exposure modelling |
| Healthcare / pharma | Medical device supply chain breach | Cold-chain route disruption |
| Energy / utilities | Critical infrastructure sub-contractor | Extreme weather → logistics exposure |

### Audience-specific emphasis
| Audience | Emphasise | De-emphasise |
|----------|-----------|--------------|
| CISO | Tier-2 visibility, `erp_visibility` punchline, real threat signal source (CISA KEV) | Data infrastructure details |
| Data Architect | Zero-ETL, Presto federation, three-source join, no data movement | Business story detail |
| IT Director | Platform consolidation, no separate AI cloud, MMA acceleration readiness | SQL-level details |
| Supply-chain / Procurement | Exposure surfaced before Monday's report, PO impact numbers | Technology platform details |
| C-suite / CEO | Speed of insight, business risk surfaced in under a second, platform modernisation story | All technical detail |

---

## Step 5: Produce the Story Brief

Write a short paragraph (3–5 sentences) the seller can say verbatim at the start of the demo.
Format:

> **[Customer name] runs [IBM i / Oracle on AIX].** Their core ERP holds the order book —
> but their operational supplier data lives in a separate system, invisible to the ERP.
> **Today, when [relevant risk event: a supplier breach / a route closure] hits, the team
> has to pull reports manually — that takes [hours / days].** This demo shows what it looks
> like when watsonx.data federates those sources in real time — on IBM Power — with no data
> movement and no ETL pipeline to maintain.

---

## Step 6: Produce Anticipated Objections

Always prepare responses to:

1. **"Is this real data?"**
   > "Yes. The IBM i is a real Power10 LPAR on TechZone running actual Db2 for IBM i.
   > PostgreSQL/EDB is running on a real RHEL Power10 VM. watsonx.data is the production
   > SaaS service on IBM Cloud. The signal injection is synthetic — that's intentional,
   > so the demo is deterministic and the story lands cleanly every time."

2. **"Does watsonx.data work on IBM Power on-premises, or only as SaaS?"**
   > "Both. This demo uses SaaS for convenience. watsonx.data is available as software on
   > IBM Power — you can run the lakehouse layer on-prem if data sovereignty requires it."

3. **"How is this different from ETL?"**
   > "ETL moves data — you make a copy, it goes stale, you manage pipelines. Federation
   > leaves data where it is. The query goes to the source, the result comes back.
   > The tier-2 supplier graph never left PostgreSQL/EDB. IBM i never exported anything.
   > That's the zero-ETL story."

4. **"What about Oracle compatibility for Path B?"**
   > "EDB Postgres Advanced Server is Oracle-compatible — same DDL, same stored procedure
   > syntax. You can migrate Oracle workloads to EDB on IBM Power without rewriting application
   > logic. That's the migration story. This demo shows the federation story — but the same
   > EDB instance that replaces Oracle is also the one watsonx.data federates against."

---

## Tester Prompt (for team validation)

When a team member is testing this recipe for the first time, they should say:

> *"I want to run the watsonx.data Power demo. My customer is [a large UK retailer / a German
> manufacturer / a financial services firm]. They run [IBM i / Oracle on AIX]. Their main
> concern is [supply-chain visibility / modernisation / real-time risk]. Help me choose the
> right path and tailor the story, then take me through deployment."*

Bob will activate this skill and guide them through the story phase before touching any infrastructure.
