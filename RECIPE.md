---
name: watsonx-data-power-demo
title: "watsonx.data on IBM Power — Zero-ETL Data Federation Demo"
description: >
  A platform-reality pre-sales demo showing how watsonx.data federates across IBM i (Db2),
  PostgreSQL on RHEL/Power, and a live event stream — on IBM Power. Two scenarios: a tier-2
  supplier cyber breach and a freight corridor closure, both surfaced via live Presto federation
  through a Carbon Design System dashboard. No mock data, no cloud AI dependency.
author: EMEA AI on IBM Power Squad
version: 1.1.0
recipe: 01-watsonx-data-power-demo.md
tags:
  - ibm-power
  - watsonx-data
  - data-federation
  - zero-etl
  - ibm-i
  - edb
  - postgresql
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
  - pre-sales-demo
techzone:
  watsonx_data_dev_image:
    collection_url: https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power
    platform_id: 685705e13f60074883ce964f
    infrastructure: ibmcloud-2
    reservation: manual
    auth: Basic (ibmlhadmin / password) — no IAM API key needed
    note: >
      watsonx.data Developer Base Image 2.2.0 GA. Note the FQDN, Presto port, SSH port,
      and UI port from the reservation Published Services tab. Provisioning takes ~20 min.
  ibm_i_plus_rhel:
    collection_url: https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power
    platform_id: 6aa0476b0e167e33005b104d
    infrastructure: systems-onprem
    reservation: manual
    note: >
      Combined IBM i + RHEL on Power (TxC Lab, Poughkeepsie). Both VMs share a /28 subnet.
      RHEL hosts PostgreSQL 16, Satellite agent, and the demo UI. IBM i hosts Db2 OLIST
      schema (Path A only). Download the SSH private key from the reservation details.
      Provisioning takes ~30 min.
  satellite_connector:
    collection_url: https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power
    platform_id: 6a8eefb1116ff35215509bbd
    infrastructure: ibmcloud-2
    reservation: manual
    note: >
      IBM Cloud Satellite Connector (ITZ-V2 account). Bridges the Dev Image (eu-de) to the
      on-prem RHEL/IBM i environments via Link endpoints on ports :5432 (PostgreSQL) and
      :8471 (IBM i DRDA). The Satellite Connector ID and IAM API key are stable across
      reservations for the same IBM Cloud account — already in setup/_start_satellite_agent.py.
      Accept the ITZ-V2 account invite via the IBM Cloud notification bell before use.
      Provisioning takes ~5 min.
db_path_variants:
  path_a_ibm_i_plus_postgresql:
    label: "Path A — IBM i + PostgreSQL (default)"
    description: IBM i Db2 as ERP source, PostgreSQL 16 as operational DB
    audience: Customers running IBM i workloads
  path_b_postgresql_only:
    label: "Path B — PostgreSQL only (EDB / Oracle replacement story)"
    description: No IBM i — EDB/PostgreSQL holds all data; positions EDB as Oracle replacement on Power
    audience: Customers running Oracle on AIX, considering modernisation to EDB on IBM Power
---
