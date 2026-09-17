---
name: watsonx-data-power-demo
title: "watsonx.data on IBM Power — Zero-ETL Data Federation Demo"
description: >
  Deploy a live, multi-source federated data demo showing how watsonx.data
  federates across IBM i (core ERP), PostgreSQL/EDB (operational DB), and an
  Apache Iceberg event stream — on IBM Power. Demonstrate real-time cyber and
  logistics signal detection with sub-second federated query response, surfaced
  through a Carbon Design System dashboard. Two DB path variants: IBM i + PostgreSQL
  (for IBM i customers) or AIX + EDB (for Oracle-on-AIX customers, EDB as Oracle
  replacement). No mock UIs, no simulated data, no cloud AI dependency.
author: EMEA AI on IBM Power Squad
version: 1.0.0
repository: https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo
tags:
  - ibm-power
  - watsonx-data
  - data-federation
  - zero-etl
  - ibm-i
  - edb
  - postgresql
  - iceberg
  - carbon-design-system
  - supply-chain
  - cyber-intelligence
  - rhel
  - ppc64le
  - pre-sales
  - platform-reality-demo
skills:
  - deploy-watsonx-data-power
  - watsonx-data-power-story-builder
modes:
  - watsonx-data-power-demo
techzone:
  watsonx_data_saas:
    collection_url: https://techzone.ibm.com/collection/watsonx-data
    infrastructure: cloud
    note: >
      watsonx.data SaaS (IBM Cloud, eu-gb). Reserve as "Demo" purpose with
      an opportunity code, or as "Test" (4-day window, no opportunity code needed).
      Bob CANNOT auto-reserve this — manual reservation required (~5 min effort,
      ~20 min provisioning wait).
  ibm_i_path:
    collection_url: https://techzone.ibm.com/collection/power-systems-with-ibm-i
    infrastructure: systems-onprem
    note: >
      IBM i LPAR on Power10. Manual reservation required (v1 TechZone environment).
      Provides the core ERP data source (Db2 for IBM i, OLIST schema).
      Path A only — skip if running the AIX + EDB path.
      SSH key-based auth. Download private SSH key from reservation details.
  rhel_power10_vm:
    collection_url: https://techzone.ibm.com/collection/generative-ai-demos-on-ibm-power
    infrastructure: systems-2
    note: >
      RHEL on Power10 (ppc64le). Manual reservation required (v1 TechZone environment).
      Hosts PostgreSQL 16 (EDB-positioned operational/ERP DB) and the Next.js demo UI.
      Required for both paths. For Path B (AIX+EDB), holds the full Olist dataset.
db_path_variants:
  ibm_i_plus_postgresql:
    description: Default path — IBM i (Db2) as ERP source, PostgreSQL 16 as operational DB
    audience: Customers already running IBM i workloads
  aix_plus_edb:
    description: AIX+EDB path — IBM i not used; EDB/PostgreSQL holds all data (Oracle replacement story)
    audience: Customers running Oracle on AIX, considering modernisation to EDB on IBM Power
---

# watsonx.data on IBM Power — Zero-ETL Data Federation Demo

For a one-page getting started guide, see [`GETTING-STARTED.md`](GETTING-STARTED.md).

For full setup instructions, see [`COLLECTION.md`](COLLECTION.md).

For the development journey, decisions, and deployment log, see [`RECIPE-JOURNEY.md`](RECIPE-JOURNEY.md).

## Quick Start

1. **Story phase** — Tell Bob: *"I want to run the watsonx.data Power demo. My customer is [name/industry/audience]. They run [IBM i / Oracle on AIX]."*
2. **Reserve** environments manually — watsonx.data SaaS + IBM i (Path A only) + RHEL/Power10 VM (~15 min effort + ~30 min wait each)
3. **Deploy** — Tell Bob your RHEL FQDN, SSH key path, and watsonx.data credentials. Bob loads data, configures federation, and deploys the UI.
4. **Demo** — Open `http://<fqdn>:3000`. Run the 6-step arc live.

**Total human effort:** ~45 minutes. **Total elapsed:** ~90 minutes (mostly TechZone provisioning waits).

> **⚠️ All TechZone reservations are manual** — IBM i, RHEL/Power10, and watsonx.data SaaS
> all use v1 TechZone environments. Bob cannot book them automatically. See `COLLECTION.md`
> for exact URLs and what to note from each reservation.
