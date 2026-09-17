# 🌐 Checkpoint Topic — Active TechZone Environments

_Referenced from `_checkpoint.md`. Content for TechZone reservations only._

## 🆕 NEW RESERVATIONS — Session 6 (2026-09-17)

| Reservation | Request ID | Env Key | Expires | Status |
|---|---|---|---|---|
| On-prem IBM i + RHEL | `6aaabd3afd09876e26e6a6ad` | `jkf6fl2k` | 2026-09-21T07:30Z | ✅ Ready |
| IBM Cloud Satellite | `6aaabe3f304e6b230f866ad3` | — | 2026-09-21T07:05Z | ✅ Ready |
| watsonx.data SaaS | `6aabd7dfe00bd16e25b73a52` | `tqj6kn2k` | 2026-09-21T12:20Z | ✅ Ready |

All three reservations are **confirmed Ready** via TechZone API as of 2026-09-17. All previous reservations have expired. Only the three above are active.

---

## ⚠️ Architecture Decision — PowerVS + Satellite (recorded this session)

**Problem discovered:** The current IBM i (`p1320`) and RHEL (`p1387`) reservations are on
different TechZone on-prem pods. `129.40.98.210` (RHEL) cannot reach `129.40.95.187` (IBM i)
— 100% packet loss confirmed. watsonx.data SaaS (IBM Cloud `eu-gb`) also cannot reach either
VM — `Connection failed` confirmed at the API level.

**Root cause:** TechZone on-prem reservations from different collections land on isolated
network pods with no L3 routing between them. IBM Cloud SaaS has no path to TechZone intranet
without an explicit bridge.

**Agreed architecture going forward:**
- **IBM i and RHEL** → both from [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84), **same geography (eu-gb)**. PowerVS instances in the same workspace share a private network natively.
- **watsonx.data SaaS → PowerVS** bridge → **IBM Cloud Satellite** Location agent on the RHEL VM. Agent makes outbound-only connections; no inbound firewall rules needed.
- **Satellite Link endpoints** expose IBM i `:8471` and PostgreSQL `:5432` as IBM Cloud-reachable hostnames for the federation connector registration.
- **IBM VPN** still needed for browser access to demo UI; not needed for service-to-service connectivity.

**Current environments (on-prem, expiring):** Kept alive for UI dev/testing only. Do not attempt federation wiring on these — networking will not work.

**Combined on-prem reservation (IBM i + RHEL in one reservation, same network pod):**
Use the **IBM i + RHEL Lab for TxC** collection: https://techzone.ibm.com/collection/ibm-i--rhel-lab-for-txc
This provisions both IBM i and RHEL into the same on-prem pod in a single reservation, solving the cross-pod networking issue seen with separate reservations.

### 6. IBM i + RHEL Combined On-Prem (TxC Lab) ✅ Ready — **ACTIVE — NEW RESERVATION (session 6)**
| Field | Value |
|---|---|
| **Request ID** | `6aaabd3afd09876e26e6a6ad` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6aaabd3afd09876e26e6a6ad |
| **Environment ID** | `6aaabd3f4f6e3e14d9979cfb` |
| **Environment key** | `jkf6fl2k` |
| **Collection** | [Show Business Value of watsonx.data with IBM Power](https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power) |
| **Status** | ✅ Ready — provisioned 2026-09-17T07:30:00Z |
| **Expires** | 2026-09-21T07:30:00Z |
| **Domain** | `p637.pok-systems.techzone.ibm.com` |
| **Subnet** | `129.40.125.64/28` |
| **VLAN** | 637 |
| **SSH user (both VMs)** | `U8GO7IL` |
| **OS password (both VMs)** | `0@0PJp+*eB3j)Vq` — used for IBM i Db2 JDBC auth (watsonx.data federation) and password-based SSH fallback |
| **SSH key** | `C:\Users\029878866\Downloads\jkf6fl2k_key.pem` (renamed from `user_ssh_private_key (6).user`) |
| **RHEL label** | `rhel-server` |
| **RHEL FQDN** | `pvm01-jkf6fl2k.p637.pok-systems.techzone.ibm.com` |
| **RHEL IP** | `129.40.125.69` |
| **RHEL OS** | RHEL 9.8 on Power10 (power architecture) |
| **RHEL specs** | 4 vCPU, 32 GB RAM, 500 GB extra disk |
| **IBM i label** | `ibmi-server` |
| **IBM i FQDN** | `pvm02-jkf6fl2k.p637.pok-systems.techzone.ibm.com` |
| **IBM i IP** | `129.40.125.73` |
| **IBM i OS** | IBM i V7R6TR1 on Power11 (power architecture), 1 vCPU, 2 GB RAM |
| **Network** | Both VMs on same `/28` subnet (129.40.125.64/28, VLAN 637) — VM-to-VM connectivity expected on port 8471 (Db2 for i) and port 5432 (PostgreSQL) |
| **⚠️ Previous reservation** | `6aa029199f3cc7ab3a08b99c` (expired 2026-09-12) — do not use its credentials or FQDNs |

---

## 7. IBM Cloud Satellite ✅ Ready — **ACTIVE — NEW RESERVATION (session 6)**
| Field | Value |
|---|---|
| **Request ID** | `6aaabe3f304e6b230f866ad3` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6aaabe3f304e6b230f866ad3 |
| **Status** | ✅ Ready — provisioned 2026-09-17T07:00:00Z |
| **Expires** | 2026-09-21T07:05:00Z |
| **IBM Cloud account** | `ITZ-V2` (account ID: `ead8711ba2cc4d08a16fd37427f4f01a`) — use account switcher dropdown, not default login |
| **⚠️ Connector status** | **NOT YET CONFIRMED for this reservation** — TechZone detail API returns 404 for the Satellite request ID. Must log into ITZ-V2 account and run `ibmcloud sat connector ls` to confirm connector ID. Previous reservation reused the same connector (`wxd-power-connector`) — may happen again. |
| **Previous Connector ID** | `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI` (may still be valid if reused) |
| **Connector name** | `wxd-power-connector` (expected name) |
| **Connector IAM API key** | `e21ytQOcIANGVrHJaqRyAhysRhtV2-VUevt9fISRG4IO` |
| **Endpoints — status** | ✅ All 3 confirmed correct (2026-09-17) |
| **pg-olist endpoint** | `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` → `127.0.0.1:5432` ✅ |
| **ibmi-db2 endpoint** | `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` → `129.40.125.73:8471` ✅ |
| **wxd-presto endpoint** | `localhost:29999` (on RHEL) → `ff5b1b42-0d0a-4d03-ac39-b4529cbda74c.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud:32564` ✅ updated |
| **wxd-presto endpoint ID** | `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI_sebnu` |
| **⚠️ ITZ-V2 account access** | Must accept invite via **notification bell** at cloud.ibm.com before account is accessible. No email is sent — check the bell icon. Then use the **account switcher dropdown** to select `2112072 - ITZ-V2`. |

---

## 4. IBM i 7.6 PowerVS (Madrid `mad02`) ⏳ Provisioning
| Field | Value |
|---|---|
| **Request ID** | `6a9a9ca586e74f3c88738eea` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6a9a9ca586e74f3c88738eea |
| **Collection** | [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84) → IBM i 7.6 IBM Cloud PowerVS VSI |
| **Datacenter** | `mad02` (Madrid) |
| **Network Config** | **Public and Private** (customised in Step 5 Configuration) |
| **Cloud Account** | `itz-shared-power` |
| **Public IP** | _Pending provisioning_ |
| **Private IP** | _Pending provisioning_ |
| **Hostname** | _Pending provisioning_ |
| **SSH user** | `ITZUSER` |
| **SSH key** | Download from reservation once Ready → "Deployment SSH private key" |
| **SSH port** | 22 |
| **Db2 for i port** | 8471 |
| **CPU / Memory** | 0.5 vCPU / 4 GB |
| **Expires** | _Pending provisioning_ |

## 5. RHEL 9 PowerVS (Madrid `mad02`) ⏳ Provisioning
| Field | Value |
|---|---|
| **Request ID** | `6a9a9d2a44fe189b4ce4b301` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6a9a9d2a44fe189b4ce4b301 |
| **Collection** | [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84) → Red Hat 9 IBM Cloud PowerVS VSI |
| **Datacenter** | `mad02` (Madrid) — matches IBM i ✅ |
| **Network Config** | **Public and Private** (customised in Step 5 Configuration) |
| **Cloud Account** | `itz-shared-power` — matches IBM i ✅ |
| **Public IP** | _Pending provisioning_ |
| **Private IP** | _Pending provisioning_ |
| **Hostname** | _Pending provisioning_ |
| **SSH user** | `itzuser` |
| **SSH key** | Download from reservation once Ready → "Deployment SSH private key" |
| **SSH port** | 22 |
| **CPU / Memory** | 0.5 vCPU / 4 GB |
| **Expires** | _Pending provisioning_ |
| **⚠️ Key note** | New VM — old `rhel_key.user` does NOT work. Must download fresh key from reservation. |
| **Satellite Connector** | TBD — `itz-shared-power` account; need to check if Connector creation is permitted |
| **PostgreSQL** | Not yet installed |
| **Demo UI** | Not yet deployed |

---

## 1. watsonx.data SaaS ✅ Ready — **ACTIVE — NEW RESERVATION (session 6)** (`tqj6kn2k`)
| Field | Value |
|---|---|
| **Request ID** | `6aabd7dfe00bd16e25b73a52` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6aabd7dfe00bd16e25b73a52 |
| **Environment ID** | `itz-110000sg2k-tqj6kn2k` |
| **Environment key** | `tqj6kn2k` |
| **Status** | ✅ Ready — provisioned 2026-09-17T12:20:00Z |
| **Expires** | 2026-09-21T12:20:00Z |
| **Region** | `eu-gb` (London) — service provisions in London despite TechZone placement in `fra04`/`eu-de` |
| **IBM Cloud Login URL** | https://cloud.ibm.com/authorize/itzwatsonx |
| **IBM Cloud Logout URL** | https://cloud.ibm.com/logout |
| **IBM Cloud account** | `itz-watsonx` — use account switcher to `itz-watsonx` (NOT ITZ-V2) |
| **Iceberg catalog name** | `wxd_tqj6kn2k` ← use this exact name in the wizard |
| **Student App ID credentials** | `student_tqj6kn2k_6aabd7e37abf28461499b835_1@techzone.ibm.com` / `dhiuevfoz0scgpw` |
| **Service API Key** | `dBtUhP7tpCUKn4NjFYEAo4-qj2HL58NBArXn5D4jBYj9` |
| **Service ID** | `itz-110000sg2k-tqj6kn2k` |
| **Instance name** | `itz-110000sg2k-tqj6kn2k` |
| **Instance GUID** | `6652674b-71c8-449d-84d6-fc06a0a7e891` ✅ confirmed — TechZone reuses the same underlying IBM Cloud service instance across reservations in the same account |
| **Instance CRN** | `crn:v1:bluemix:public:lakehouse:eu-gb:a/9f8f95eee4714473a87fa319d964063c:6652674b-71c8-449d-84d6-fc06a0a7e891::` ✅ |
| **Resource group ID** | `898367f9b5354357943800da864aefcc` |
| **Created** | 2026-09-17 by `IBMid-666000YO0V` |
| **Presto engine name** | `Starter` |
| **Presto engine ID** | `prismo970` |
| **Presto engine hostname** | ⏳ retrieve via tunnel after Satellite agent connected |
| **Wizard status** | ✅ **Completed** — engine RUNNING as of 2026-09-17 14:41 GMT+1. Catalog `wxd_tqj6kn2k` created, COS bucket auto-accepted, Prestissimo C++ (Gluten 3.5) RUNNING, catalog already associated to engine in topology. |
| **⚠️ Wizard prerequisite** | Accept `itz-watsonx` invite via **notification bell** BEFORE opening console. Use student App ID only — never IBM ID. Open incognito → `https://cloud.ibm.com/authorize/itzwatsonx` |
| **⚠️ Previous reservation** | `6aa43072e182c81b8c7ff43e` (`limql82k`) — expired. Do not reuse any CRN, GUID, or catalog name from it. |

### ⚠️ Definitive watsonx.data Setup Procedure (2026-09-11 — hard-won)

The API changed significantly between Aug and Sep 2026. The wizard is the only reliable path. Follow this exactly:

**Pre-requisites:**
1. Accept the `itz-watsonx` account invitation via the **notification bell** at cloud.ibm.com (IBM ID session, normal browser). The invite may come from an earlier reservation — the link is valid 30 days and still works.
2. Log **completely out** of all IBM Cloud sessions in normal browser. Close all browser windows.
3. Open a **fresh incognito/private** window. Go to `https://cloud.ibm.com/authorize/itzwatsonx`. Log in with the **student App ID credentials** from the reservation page (e.g. `student_7jtdt22k_1@techzone.ibm.com`). Never use IBM ID for the watsonx.data console.

**Wizard steps:**
4. The first screen may show "initial sandbox setup" — this is correct and means MDS is initialising under the right identity. Let it complete.
5. Select **"Run scalable analytics and data processing workloads"** (Presto). Click Next.
6. When asked for catalog name: use **a name unique to your reservation** — e.g. `wxd_<env-key-suffix>` (the 8-char suffix from the environment ID, visible on the reservation page). Do NOT use `iceberg_data` — it is permanently taken in the shared `itz-watsonx` MDS namespace by previous users/reservations and will always 400.
7. Accept the auto-discovered COS bucket. Do not create a new one.
8. Finish. The engine will show PROVISIONING — this is normal, takes 5–10 minutes.

**If the wizard gives a 400 on the bucket/catalog step:**
- Most likely cause: a stale storage registration exists from a previous API call or failed wizard run.
- Fix: delete it via API, then retry the wizard immediately:
  ```python
  # Get IAM token first, then:
  requests.delete(
      f'https://eu-gb.lakehouse.cloud.ibm.com/lakehouse/api/v3/{instance_guid}/storage_registrations/{bucket_id}',
      headers={'Authorization': 'Bearer '+token, 'AuthInstanceId': crn, 'iamToken': token, 'LhInstanceId': instance_guid}
  )
  ```
- The bucket ID is the same as the bucket name (e.g. `watsonx-data-3d6fbad3-...`).

**What NOT to do:**
- Do not run `setup/4-provision-via-rest-api.py` before the wizard. The `storage_registrations` API no longer accepts `associated_catalogs` in the POST body (schema changed Sep 2026). Registering the bucket via API before the wizard runs causes a `duplicate key` 400 that blocks the wizard.
- Do not try to create the catalog via `POST /lakehouse/api/v3/catalogs` — this endpoint only allows GET.
- Do not try to create the engine via API until the catalog exists — the node_type/size_config validation is stricter now and the wizard-created engine is the reliable path.

**After wizard completes — verify via API:**
```python
# All three should return non-empty results:
GET /lakehouse/api/v3/{instance_guid}/storage_registrations  → bucket active
GET /lakehouse/api/v3/catalogs                               → catalog present
GET /lakehouse/api/v3/{instance_guid}/prestissimo_engines    → engine PROVISIONING→RUNNING
```

**Auth headers required (two extras needed for /storage/cos/* endpoints):**
```
Authorization: Bearer <IAM token>
AuthInstanceId: <full CRN>
iamToken: <IAM token>        ← required for /storage/cos/* endpoints
LhInstanceId: <instance_guid> ← required for /storage/cos/* endpoints
```
IAM token obtained via: `POST https://iam.cloud.ibm.com/identity/token` with `grant_type=urn:ibm:params:oauth:grant-type:apikey` and the TechZone Service API Key.

### watsonx.data v3 REST API — endpoint notes (updated 2026-09-11)
- `POST /lakehouse/api/v3/{instance_guid}/storage_registrations` — registers COS bucket only (no `associated_catalogs` in body — schema changed, that field is now rejected). Use for cleanup/verification, not initial setup.
- Catalog creation is handled internally by the wizard via `GET/POST /lakehouse/api/v3/{instance_guid}/storage/cos/buckets` — not directly accessible without browser session token.
- `POST /lakehouse/api/v3/{instance_guid}/prestissimo_engines` — creates engine. `size_config: starter` requires specific node_type values — use wizard, not API, for initial engine creation.
- `GET /lakehouse/api/v3/catalogs`, `GET /lakehouse/api/v3/{instance_guid}/prestissimo_engines` — reliable for verification.
- `DELETE /lakehouse/api/v3/{instance_guid}/storage_registrations/{bucket_id}` — 204 on success. Use to clear stale registrations before re-running wizard.

## 2. IBM i 7.6 TR1 on Power10 ✅ Ready
| Field | Value |
|---|---|
| **Request ID** | `6a86ef7c59ed58edc75cdf0a` |
| **TechZone URL** | https://techzone.ibm.com/my/requests/6a86ef7c59ed58edc75cdf0a |
| **IP Address** | `129.40.95.187` |
| **FQDN** | `pvm1-4o2fhf0k.p1320.pok-systems.techzone.ibm.com` |
| **OS User** | `UD7XZDE` |
| **OS Password** | `l80YdO@6I.mhZMi` |
| **Architecture** | Power10, 2 vCPU, 4 GB RAM, shared |
| **Expires** | 2026-08-24T12:10:00Z — **⚠️ Extend soon** (deferred — not urgent today) |
| **Access** | IBM Cisco AnyConnect VPN required for IBMers |

## 3. RHEL/Power10 VM ✅ Ready
| Field | Value |
|---|---|
| **Request ID** | `6a883b7f373b084fda04ed7e` |
| **FQDN** | `pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com` |
| **SSH User** | `UB4YVFN` |
| **SSH Key** | `C:\Users\029878866\Downloads\rhel_key.user` (copied from `user_ssh_private_key (1).user` — parentheses in filename broke shell quoting) |
| **SSH Password** | `9JNEyS)(qb1a5Q1` (fallback — key auth now confirmed working) |
| **Architecture** | Power10, ppc64le |
| **OS** | **RHEL 10.2** (Coughlan) — not RHEL 8 as originally noted |
| **Node.js** | v24.18.0 installed as `nodejs24` — symlinked to `/usr/local/bin/node` and `npm` |
| **Demo UI** | ✅ Running at `http://pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com:3000` — Next.js 13.4.9, started with `PORT=3000 nohup npm start > ~/demo-ui.log 2>&1 & disown $!` from `~/watsonx-data-power-demo/demo-ui/` |
| **Purpose** | PostgreSQL operational DB (Source 2) + demo UI |
| **Access** | IBM Cisco AnyConnect VPN required for IBMers |
| **fapolicyd** | Not active — no allow rules needed |
| **firewalld** | Not running — port 3000 open by default |
| **PostgreSQL** | ✅ PostgreSQL 16 installed via PGDG repo (`/usr/pgsql-16/bin/psql`), running on port 5432, service `postgresql-16`. EDB AS repo returns 404 for ppc64le (token-gated, no ppc64le packages published). Community PostgreSQL 16 is the correct choice — functionally identical for watsonx.data federation. |
| **PostgreSQL data** | ✅ `olist` database loaded: 50 tier-2 suppliers (4 COMPROMISED), 3,095 suppliers, 23 warehouses, 112,650 purchase orders. User `edbadmin` / password `edbadmin1`. |
