# 🌐 Checkpoint Topic — Active TechZone Environments

_Referenced from `_checkpoint.md`. Content for TechZone reservations only._

---

## 🆕 NEW RESERVATIONS — Session 16 (Current)

| Environment | Status | Key details |
|---|---|---|
| **IBM i + RHEL (On-prem)** | ✅ Ready | SSH user `UHJ907M`, domain `p604.pok-systems.techzone.ibm.com` |
| **IBM Cloud Satellite** | ✅ Ready | ID `6abe30c2db5476036233b2a2`, account `ead8711ba2cc4d08a16fd37427f4f01a` |
| **watsonx.data Dev Image** | ✅ Ready | SSH port `44574`, Presto port `48872`, host `eu-de.services.cloud.techzone.ibm.com` |

---

## 1. IBM i + RHEL Combined On-Prem (Session 16 — CURRENT)

| Field | Value |
|---|---|
| **SSH user (both VMs)** | `UHJ907M` |
| **OS password (both VMs)** | `v07zF-4WDyP_a4x` — used for IBM i Db2 DRDA auth and SSH fallback |
| **SSH key** | `C:\Users\029878866\Downloads\pvm-4r13fr3k-key.pem` (renamed from `user_ssh_private_key (10).user`) |
| **Domain** | `p604.pok-systems.techzone.ibm.com` |
| **RHEL label** | `rhel-server` |
| **RHEL FQDN** | `pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com` |
| **RHEL IP** | `129.40.252.57` |
| **RHEL OS** | RHEL 9.8 on Power |
| **IBM i label** | `ibmi-server` |
| **IBM i FQDN** | `pvm02-4r13fr3k.p604.pok-systems.techzone.ibm.com` |
| **IBM i IP** | `129.40.252.51` |
| **IBM i OS** | IBM i V7R6TR1 on Power |
| **IBM i RDB name** | `PVM02` + `4R13FR3K` suffix → likely `PVM024R13FR3K` — **verify with `DSPRDBDIRE` on IBM i** |

> **IBM i RDB name**: Run `system "DSPRDBDIRE"` via SSH to get the exact RDB name. Pattern from previous reservations: uppercase domain prefix, e.g. `PVM02XU9` for `pvm02-xu9...`. For this reservation it should be `PVM024R13FR3K` — confirm before running `7-register-catalogs.py`.

---

## 2. IBM Cloud Satellite (Session 16 — CURRENT)

| Field | Value |
|---|---|
| **Reservation ID** | `6abe30c2db5476036233b2a2` |
| **Desktop URL** | https://cloud.ibm.com/satellite/locations?bss_account=ead8711ba2cc4d08a16fd37427f4f01a |
| **IBM Cloud account ID** | `ead8711ba2cc4d08a16fd37427f4f01a` |
| **IBM Cloud API key** | `MH_j3NAOnqXLvgu1Z34KPa38MW6h_KtVyzr_BB7gVHyE` |
| **Satellite connector** | Re-confirm via `ibmcloud sat connector ls` — connector name `wxd-power-connector` likely reused |
| **pg-olist endpoint** | Satellite Link → `127.0.0.1:5432` (RHEL localhost PostgreSQL) — **port TBD after connector check** |
| **ibmi-db2 endpoint** | Satellite Link → `129.40.252.51:8471` (IBM i DRDA) — **port TBD after connector check** |

> **Action needed**: Log into IBM Cloud (account `ead8711ba2cc4d08a16fd37427f4f01a`), go to Satellite → Connectors → `wxd-power-connector`, and note the current endpoint ports. Update `IBMI_PORT` and `PG_PORT` in `7-register-catalogs.py` accordingly.

---

## 3. watsonx.data Dev Image (Session 16 — CURRENT)

| Field | Value |
|---|---|
| **Host** | `eu-de.services.cloud.techzone.ibm.com` |
| **SSH port** | `44574` (service 22 mapping) |
| **SSH user** | `watsonx` (fixed for Dev Image) |
| **SSH password** | `watsonx.data` (fixed for Dev Image) |
| **Presto console** | https://eu-de.services.cloud.techzone.ibm.com:48872 |
| **Presto port** | `48872` |
| **Watsonx UI** | https://eu-de.services.cloud.techzone.ibm.com:48209 |
| **Portainer** | http://eu-de.services.cloud.techzone.ibm.com:43511 |
| **Diagnostic Console** | http://eu-de.services.cloud.techzone.ibm.com:44121 |
| **Jupyter Notebook** | http://eu-de.services.cloud.techzone.ibm.com:27838/notebooks/Table_of_Contents.ipynb |
| **Minio Endpoint** | `eu-de.services.cloud.techzone.ibm.com:20469` |
| **Minio console** | http://eu-de.services.cloud.techzone.ibm.com:25931 |
| **Thrift URL** | `thrift://eu-de.services.cloud.techzone.ibm.com:27615` |
| **Postgres Port (internal)** | `eu-de.services.cloud.techzone.ibm.com:25786` |
| **Db2 Port** | `eu-de.services.cloud.techzone.ibm.com:31557` |
| **Milvus REST** | `eu-de.services.cloud.techzone.ibm.com:38103` |
| **Milvus Port** | `eu-de.services.cloud.techzone.ibm.com:33652` |
| **Open Port 1 (10000)** | `eu-de.services.cloud.techzone.ibm.com:34391` |
| **Open Port 2 (10001)** | `eu-de.services.cloud.techzone.ibm.com:49207` |

---

## Satellite Endpoint Ports — Status

Satellite endpoint ports for this reservation are **not yet confirmed**. Previous reservations used:
- `pg-olist`: port `33156` → `127.0.0.1:5432`
- `ibmi-db2`: port `33180` → `129.40.252.73:8471` (old reservation IP)

For session 16, IBM i IP is `129.40.252.51`. Endpoint target needs updating if connector was recreated.
Check via IBM Cloud console or `ibmcloud sat endpoint ls --connector-id <ID>`.

---

## Previous Sessions (archived)

Previous reservation details (sessions 1–15) are in git history. Key sessions:
- **Session 6 (2026-09-17)**: First working cross-catalog join. Used `UVU2BTL` / `PVM02XU9` / `p637` domain.
- **Session 15**: Introduced `get_lh_token()` JWT auth; all three environments were provisioning at end of session.
