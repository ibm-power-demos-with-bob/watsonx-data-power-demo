-- ============================================================================
-- 11. PostgreSQL — Compatibility views for watsonx.data Prestissimo (C++) federation
-- ============================================================================
-- Purpose:
--   The watsonx.data Prestissimo (Presto C++) connector does not support
--   PostgreSQL CHAR(n) columns — it throws "Unknown type char(n)" at scan time,
--   before any query-level CAST can help.  This is a connector-level limitation
--   specific to Presto C++; the Java connector has a partial workaround but C++
--   does not.
--
--   These views re-expose every CHAR(n) column as VARCHAR(n) so the connector
--   only ever sees types it can map.  The base tables are unchanged.
--
--   Affected columns across the olist schema:
--     suppliers:       supplier_id CHAR(32), state CHAR(2),
--                      currency_code CHAR(3), country_code CHAR(2)
--     purchase_orders: order_id CHAR(32), supplier_id CHAR(32),
--                      currency_code CHAR(3)
--     warehouses:      state CHAR(2), currency_code CHAR(3), country_code CHAR(2)
--     tier2_suppliers: country_code CHAR(2)
--
--   The federated queries in the demo UI target these views, not the base tables.
--
-- Run via SSH on the RHEL VM:
--   psql -h localhost -U edbadmin -d olist -f /tmp/pg_compat_views.sql
-- ============================================================================

-- Drop and recreate so the script is idempotent
DROP VIEW IF EXISTS olist.v_tier2_suppliers CASCADE;
DROP VIEW IF EXISTS olist.v_suppliers       CASCADE;
DROP VIEW IF EXISTS olist.v_warehouses      CASCADE;
DROP VIEW IF EXISTS olist.v_purchase_orders CASCADE;

-- ---------------------------------------------------------------------------
-- v_tier2_suppliers  (only country_code is CHAR)
-- ---------------------------------------------------------------------------
CREATE VIEW olist.v_tier2_suppliers AS
SELECT
    tier2_id,
    company_name,
    company_code,
    service_type,
    region_label,
    CAST(country_code  AS VARCHAR(2))   AS country_code,
    breach_status,
    breach_notified,
    cve_reference
FROM olist.tier2_suppliers;

-- ---------------------------------------------------------------------------
-- v_suppliers  (supplier_id, state, currency_code, country_code are CHAR)
-- ---------------------------------------------------------------------------
CREATE VIEW olist.v_suppliers AS
SELECT
    CAST(supplier_id    AS VARCHAR(32))  AS supplier_id,
    zip_code,
    city,
    CAST(state          AS VARCHAR(2))   AS state,
    region_label,
    CAST(currency_code  AS VARCHAR(3))   AS currency_code,
    CAST(country_code   AS VARCHAR(2))   AS country_code,
    subcontracted_to_id
FROM olist.suppliers;

-- ---------------------------------------------------------------------------
-- v_warehouses  (state, currency_code, country_code are CHAR)
-- ---------------------------------------------------------------------------
CREATE VIEW olist.v_warehouses AS
SELECT
    warehouse_id,
    warehouse_code,
    region_label,
    city,
    CAST(state          AS VARCHAR(2))   AS state,
    capacity_sqm,
    CAST(currency_code  AS VARCHAR(3))   AS currency_code,
    CAST(country_code   AS VARCHAR(2))   AS country_code
FROM olist.warehouses;

-- ---------------------------------------------------------------------------
-- v_purchase_orders  (order_id, supplier_id, currency_code are CHAR)
-- ---------------------------------------------------------------------------
CREATE VIEW olist.v_purchase_orders AS
SELECT
    po_id,
    po_number,
    CAST(order_id       AS VARCHAR(32))  AS order_id,
    order_item_id,
    CAST(supplier_id    AS VARCHAR(32))  AS supplier_id,
    warehouse_id,
    category_en,
    unit_price,
    freight_value,
    ship_limit_date,
    po_status,
    CAST(currency_code  AS VARCHAR(3))   AS currency_code,
    created_at
FROM olist.purchase_orders;

-- ---------------------------------------------------------------------------
-- v_compromised_exposure
-- Pre-aggregated summary: one row per compromised tier-2 supplier.
-- The demo UI cyber query reads this instead of doing the full 3-way join
-- at query time — reduces Presto round-trip latency from ~5s to <1s.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS olist.v_compromised_exposure;
CREATE VIEW olist.v_compromised_exposure AS
SELECT
    t2.company_name,
    t2.service_type,
    t2.region_label                                  AS tier2_region,
    t2.cve_reference,
    t2.breach_status,
    s.currency_code,
    COUNT(po.po_id)                                  AS open_po_count,
    COUNT(DISTINCT s.supplier_id)                    AS tier1_suppliers_affected,
    SUM(po.unit_price + po.freight_value)            AS total_exposure,
    MIN(po.ship_limit_date)                          AS earliest_ship_limit,
    SUM(CASE WHEN po.po_status = 'OPEN' THEN 1 ELSE 0 END) AS critical_pos_7d
FROM olist.tier2_suppliers t2
JOIN olist.suppliers s       ON s.subcontracted_to_id = t2.tier2_id
JOIN olist.purchase_orders po ON po.supplier_id = s.supplier_id
WHERE t2.breach_status = 'COMPROMISED'
GROUP BY t2.company_name, t2.service_type, t2.region_label,
         t2.cve_reference, t2.breach_status, s.currency_code;

-- ---------------------------------------------------------------------------
-- v_wildfire_at_risk_pos
-- Pre-filtered view: open POs from suppliers in wildfire-affected regions,
-- ordered by earliest ship limit. Presto reads ~5 rows instead of joining
-- 112k purchase_orders × 23 warehouses at query time.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS olist.v_wildfire_at_risk_pos;
CREATE VIEW olist.v_wildfire_at_risk_pos AS
SELECT
    po.po_number,
    po.unit_price + po.freight_value         AS order_value,
    w.region_label                           AS supplier_region,
    po.ship_limit_date
FROM olist.purchase_orders po
JOIN olist.warehouses w ON po.warehouse_id = w.warehouse_id
WHERE w.region_label IN ('South France', 'Catalonia', 'Mediterranean')
  AND po.po_status = 'OPEN'
ORDER BY po.ship_limit_date ASC;

-- ============================================================================
-- Smoke test (run after creation to confirm):
--   SELECT supplier_id, region_label FROM olist.v_suppliers LIMIT 3;
--   SELECT po_number, supplier_id FROM olist.v_purchase_orders LIMIT 3;
--   SELECT company_name, breach_status FROM olist.v_tier2_suppliers WHERE breach_status = 'COMPROMISED';
--   SELECT company_name, open_po_count, total_exposure FROM olist.v_compromised_exposure;
--   SELECT po_number, supplier_region FROM olist.v_wildfire_at_risk_pos LIMIT 5;
-- ============================================================================
