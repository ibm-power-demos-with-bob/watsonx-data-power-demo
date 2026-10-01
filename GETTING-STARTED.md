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

#### 1. watsonx.data Developer Base Image (required for both paths)
- Go to **https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power**
- Reserve **IBM watsonx.data Development Lab - 2.2.0 GA** (VMware, `eu-de`)
- Note: Presto port (`:46662` or assigned), UI port, FQDN. Presto uses Basic auth (`ibmlhadmin`/`password`) — no IAM API key needed.

#### 2. Combined IBM i + RHEL on Power (TxC Lab)
- Go to **https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power**
- Reserve **IBM i / RHEL lab** (both VMs land on the same `/28` subnet in Poughkeepsie)
- Download the **User Private SSH Key** (`user_ssh_private_key.pem`)
- Note: RHEL IP (`129.40.125.69`), IBM i IP (`129.40.125.73`), credentials (`U8GO7IL` / `0@0PJp+*eB3j)Vq`)

#### 3. IBM Cloud Satellite Connector
- Go to **https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power**
- Reserve **IBM Satellite**
- Note: Connector name (`wxd-power-connector`) & Satellite Link endpoints

Wait for all reservations to reach **Ready** status before proceeding.

---

### Step 3 — Deploy (~30–45 min, Bob-driven)

Tell Bob your reservation details:

> *"Deploy the watsonx.data Power demo.
>  RHEL IP/FQDN: 129.40.125.69, SSH key: [path].
>  IBM i IP: 129.40.125.73.
>  watsonx.data Dev Image Presto Host: eu-de.services.cloud.techzone.ibm.com, Port: 46662."*

Bob will:
1. Confirm SSH connectivity to RHEL and IBM i
2. Start the IBM Cloud Satellite agent container on RHEL
3. Apply compatibility views & load sample data in IBM i Db2 and RHEL PostgreSQL
4. Register the Presto federation connectors (`pg_olist` and `ibmi_olist`)
5. Deploy and start the Carbon Design System demo UI on RHEL (port 3000)
6. Verify live federated query execution across all sources

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
