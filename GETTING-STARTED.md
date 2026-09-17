# Getting Started — watsonx.data on IBM Power

> **One-sentence pitch:** Show your customer how watsonx.data federates across IBM i
> (or EDB on AIX), PostgreSQL, and a live event stream — on IBM Power — reacting to a
> real-time cyber or logistics disruption in under a second, without moving a single byte.

---

## What you need

- IBM VPN active (all TechZone environments are intranet-only)
- This repo cloned locally
- IBM Bob with this collection installed

---

## Three steps

### Step 1 — Story phase (15–30 min, no infrastructure needed)

Tell Bob which customer you are running this for:

> *"I want to run the watsonx.data Power demo. My customer is [name/industry].
>  They run [IBM i / Oracle on AIX]. Their main concern is [supply-chain risk /
>  data silos / real-time insight / modernisation]."*

Bob activates the **watsonx-data-power-story-builder** skill and helps you:
- Choose the right DB path (Path A: IBM i + PostgreSQL / Path B: AIX + EDB)
- Tailor the scenario framing to your customer
- Produce talking points and anticipated objections
- Write an opening sentence you can say live

---

### Step 2 — Reserve environments (~15–45 min effort + provisioning wait)

All three environments need **manual TechZone reservation** — these are v1 environments
that Bob cannot book automatically.

#### watsonx.data SaaS (required for both paths)
- Go to **https://techzone.ibm.com/collection/watsonx-data**
- Reserve for "Demo" purpose (enter your opportunity code) or "Test" (no code needed)
- Recommended geography: **Europe (London / eu-gb)**
- Note: IBM Cloud API key + instance CRN + COS bucket name from reservation details

#### IBM i LPAR — Path A only
- Reserve from the IBM i on Power TechZone collection
- Download the **User Private SSH Key** from reservation details
- Note: FQDN/IP + user credentials (must have `*SECOFR` authority)

#### RHEL/Power10 VM (required for both paths)
- Reserve from **https://techzone.ibm.com/collection/generative-ai-demos-on-ibm-power**
  (or equivalent RHEL on Power10 IaaS collection)
- Download the **User Private SSH Key** from reservation details
- Note: FQDN

Wait for all reservations to reach **Ready** status before proceeding.

---

### Step 3 — Deploy (~30–60 min, mostly automated)

Tell Bob your reservation details:

> *"Deploy the watsonx.data Power demo.
>  Path [A / B].
>  RHEL FQDN: [fqdn]. RHEL SSH key: [local path].
>  IBM i IP: [ip]. IBM i SSH key: [local path]. IBM i user: [user]. (Path A only)
>  watsonx.data API key: [key]. CRN: [crn]. COS bucket: [bucket]."*

Bob will:
1. Confirm SSH connectivity to each environment
2. Provision watsonx.data infrastructure (Presto, Iceberg catalog, COS)
3. Load IBM i data — CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS + SECTOR (Path A)
4. Install PostgreSQL / EDB and load supplier data on RHEL (both paths)
5. Configure federation connectors in watsonx.data
6. Deploy the Carbon Design System demo UI on RHEL
7. Run a smoke test — confirm all three source connections and both alert scenarios

**Total human effort:** ~45 minutes. **Total elapsed:** ~90 minutes (mostly TechZone waits).

---

## Running the demo

Open `http://<rhel-fqdn>:3000` (IBM VPN active). The 6-step arc:

| Step | URL | What happens |
|------|-----|-------------|
| 1 | `/` | Static supply-chain report — the "old world map" view |
| 2 | `/sources` | Federation architecture — three live data sources |
| 3 | `/live?scenario=cyber` | Live POS stream → inject cyber signal → alert card fires |
| 4 | `/outcome?scenario=cyber` | Timeline: old-world 80h response vs new-world 4h |
| 5 | `/live?scenario=wildfire` | Same stream → inject wildfire signal → alert card fires |
| 6 | `/outcome?scenario=wildfire` | Timeline: old-world 96h response vs new-world 90min |

**The punchline** (cyber scenario, live in the query result):
```
erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'
```
This column exists in the real federated query result — it is not a mock. The audience
sees a data source their ERP has literally never seen, surfaced live in context.

---

## For more detail

- [`COLLECTION.md`](COLLECTION.md) — full setup instructions, both DB paths
- [`RECIPE.md`](RECIPE.md) — recipe frontmatter and quick-start
- [`RECIPE-JOURNEY.md`](RECIPE-JOURNEY.md) — full development log and decisions
- `setup/2-configure-federation.md` — watsonx.data connector configuration reference
