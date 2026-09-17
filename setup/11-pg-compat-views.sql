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

-- ============================================================================
-- Smoke test (run after creation to confirm):
--   SELECT supplier_id, region_label FROM olist.v_suppliers LIMIT 3;
--   SELECT po_number, supplier_id FROM olist.v_purchase_orders LIMIT 3;
--   SELECT company_name, breach_status FROM olist.v_tier2_suppliers WHERE breach_status = 'COMPROMISED';
-- ============================================================================
