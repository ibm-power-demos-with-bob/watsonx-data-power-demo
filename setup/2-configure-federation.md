# 🔌 Step 2: Configure Federation Catalogs in watsonx.data

watsonx.data connects to external transactional databases without copying or
moving data. This guide covers the two catalogs needed for the Retail demo:
IBM i (Db2 for i) and PostgreSQL 16.

---

## Prerequisites

- watsonx.data console open, logged in as the **student** App ID account
  (see `checkpoint-environments.md` — IBM ID has insufficient MDS permissions)
- Presto C++ engine `presto-demo` is Running
- `iceberg_data2` Iceberg catalog is associated with `presto-demo`
- IBM i LPAR is up and reachable (VPN connected for IBMers)
- PostgreSQL 16 is installed on the RHEL/Power10 VM and the port is open

---

## 1. Add IBM i Db2 Catalog (`db2_ibmi`)

### In the watsonx.data Web Console

1. Navigate to **Infrastructure Manager** → **Add component** → **Add database**.
2. Select **IBM Db2** (the Db2 for i driver uses the same connector).
3. Fill in the connection details:

   | Field | Value |
   |---|---|
   | **Display name / Catalog name** | `db2_ibmi` |
   | **Host** | `129.40.95.187` (or FQDN `pvm1-4o2fhf0k.p1320.pok-systems.techzone.ibm.com`) |
   | **Port** | `8471` (AS/400 JDBC default) |
   | **Database** | `*LOCAL` (or leave blank — JT400 connects to the default RDBNAME) |
   | **Username** | `UD7XZDE` |
   | **Password** | *(from `checkpoint-environments.md`)* |
   | **SSL** | Off (TechZone LPAR has no SSL listener on 8471) |

4. Click **Test connection** — expect green.
5. Associate with the `presto-demo` engine and click **Save**.

### Verify in Query Workspace

```sql
SHOW SCHEMAS FROM db2_ibmi;
-- Expect: OLIST (and system schemas QSYS, QSYS2, …)

SELECT COUNT(*) FROM db2_ibmi.OLIST.ORDERS;
-- Expect: 99441 (full Olist dataset)
```

---

## 2. Add PostgreSQL Catalog (`pg_olist`)

*(PostgreSQL 16 is now installed on the RHEL VM — port 5432, user `edbadmin`, database `olist`.)*

### In the watsonx.data Web Console

1. Navigate to **Infrastructure Manager** → **Add component** → **Add database**.
2. Select **PostgreSQL**.
3. Fill in the connection details:

   | Field | Value |
   |---|---|
   | **Display name / Catalog name** | `pg_olist` |
   | **Host** | `pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com` |
   | **Port** | `5432` |
   | **Database** | `olist` |
   | **Username** | `edbadmin` |
   | **Password** | `edbadmin1` |
   | **SSL** | Off for TechZone LAN |

4. Click **Test connection** — expect green.
5. Associate with the `presto-demo` engine and click **Save**.

### Verify in Query Workspace

```sql
SHOW SCHEMAS FROM pg_olist;
-- Expect: olist

SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers;
-- Expect: 50

SELECT COUNT(*) FROM pg_olist.olist.suppliers;
-- Expect: 3095
```

---

## 3. Validate 3-Source Federated Query

Once both catalogs are connected and Iceberg has some POS events from the
retail event generator, run the cross-source join to confirm federation works
end-to-end:

```sql
-- Orders from IBM i + supplier from PostgreSQL + live POS events from Iceberg
SELECT
    o.ORDER_ID,
    o.ORDER_STATUS,
    p.CATEGORY_NAME_EN                      AS product_category,
    s.city                                  AS supplier_city,
    s.region_label                          AS supplier_region
FROM db2_ibmi.OLIST.ORDERS           AS o
JOIN db2_ibmi.OLIST.ORDER_ITEMS      AS oi  ON o.ORDER_ID   = oi.ORDER_ID
JOIN db2_ibmi.OLIST.PRODUCTS         AS p   ON oi.PRODUCT_ID = p.PRODUCT_ID
JOIN pg_olist.olist.suppliers        AS s   ON s.supplier_id = oi.SELLERID
WHERE o.ORDER_STATUS = 'delivered'
LIMIT 20;
```

This query is also saved in `queries/retail-federated-query.sql`.
