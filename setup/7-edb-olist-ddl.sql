-- ============================================================================
-- 7. EDB Postgres DDL — Olist Retail Supplier/Operational Dataset
-- ============================================================================
-- Run via setup/8-load-edb-olist.py --create-schema
-- OR manually:  psql -h <host> -U edbadmin -d olist -f setup/7-edb-olist-ddl.sql
--
-- Tables held here (EDB "operational DB" layer):
--   TIER2_SUPPLIERS — Fictional logistics sub-contractors (the cyber demo victim)
--   SUPPLIERS       — Olist sellers, enriched with localisation columns
--                     Each supplier has a FK to a TIER2_SUPPLIERS row —
--                     their freight/file-transfer sub-contractor.
--   WAREHOUSES      — One synthetic warehouse per seller region/state
--   PURCHASE_ORDERS — Synthetic POs linking IBM i ORDER_ITEMS → EDB SUPPLIERS
--
-- Tier-2 narrative:
--   TIER2_SUPPLIERS are entirely fictional companies (e.g. "Nexaflow Logistics Ltd").
--   They represent the logistics sub-contractors that YOUR direct suppliers
--   (SUPPLIERS) use for managed file transfer and freight coordination.
--   They do NOT appear in the IBM i ERP at all — that is the point.
--   When the cyber incident signal fires, the federated query joins across
--   IBM i + EDB to surface exposure that is literally invisible without federation.
--
-- Localisation notes:
--   currency_code   — defaults to 'GBP'; swap to 'EUR', 'USD', etc. per audience
--   region_label    — human-readable region name (e.g. "South East England")
--                     populated from a configurable region-map at load time
--   category_en     — English category name joined from product_category_name_translation.csv
--                     so query output is readable without knowing Portuguese
-- ============================================================================

-- Drop and recreate schema for idempotent re-runs
DROP SCHEMA IF EXISTS olist CASCADE;
CREATE SCHEMA olist;

-- ---------------------------------------------------------------------------
-- TIER2_SUPPLIERS  (fully synthetic — fictional logistics sub-contractors)
-- These companies do not exist in any real dataset.  They represent the
-- layer of the supply chain that is invisible to the core ERP — the whole
-- point of the cyber incident demo narrative.
--
-- breach_status: CLEAN | COMPROMISED | SUSPECTED
--   Set to COMPROMISED for the incident victim(s) when the signal fires.
--   In the demo, the loader pre-seeds 3–4 rows as COMPROMISED to simulate
--   a breach already in progress at demo time.
-- ---------------------------------------------------------------------------
CREATE TABLE olist.tier2_suppliers (
    tier2_id        SERIAL          NOT NULL,
    company_name    VARCHAR(120)    NOT NULL,       -- fictional company name
    company_code    VARCHAR(20)     NOT NULL,       -- e.g. 'T2-NXF-001'
    service_type    VARCHAR(60),                    -- e.g. 'Managed File Transfer'
    region_label    VARCHAR(80),
    country_code    CHAR(2)         NOT NULL DEFAULT 'GB',
    breach_status   VARCHAR(20)     NOT NULL DEFAULT 'CLEAN',
    breach_notified TIMESTAMP,                      -- when breach was confirmed/notified
    cve_reference   VARCHAR(40),                    -- e.g. 'CVE-2023-34362'
    CONSTRAINT pk_tier2_suppliers PRIMARY KEY (tier2_id),
    CONSTRAINT ck_breach_status CHECK (breach_status IN ('CLEAN','COMPROMISED','SUSPECTED'))
);

CREATE UNIQUE INDEX ix_tier2_code   ON olist.tier2_suppliers (company_code);
CREATE        INDEX ix_tier2_breach ON olist.tier2_suppliers (breach_status);

-- ---------------------------------------------------------------------------
-- SUPPLIERS  (source: olist_sellers_dataset.csv)
-- subcontracted_to_id links each direct supplier to their tier-2 logistics
-- sub-contractor.  This FK is what the cyber query traverses to reveal exposure.
-- ---------------------------------------------------------------------------
CREATE TABLE olist.suppliers (
    supplier_id          CHAR(32)    NOT NULL,
    zip_code             VARCHAR(10),
    city                 VARCHAR(80),
    state                CHAR(2),                   -- original Olist state code
    region_label         VARCHAR(80),               -- localised region name for display
    currency_code        CHAR(3)     NOT NULL DEFAULT 'GBP',
    country_code         CHAR(2)     NOT NULL DEFAULT 'GB',
    subcontracted_to_id  INTEGER,                   -- FK → tier2_suppliers.tier2_id
    CONSTRAINT pk_suppliers PRIMARY KEY (supplier_id),
    CONSTRAINT fk_supplier_tier2 FOREIGN KEY (subcontracted_to_id)
        REFERENCES olist.tier2_suppliers (tier2_id) ON DELETE SET NULL
);

CREATE INDEX ix_suppliers_state  ON olist.suppliers (state);
CREATE INDEX ix_suppliers_tier2  ON olist.suppliers (subcontracted_to_id);

-- ---------------------------------------------------------------------------
-- WAREHOUSES  (synthetic — one per distinct seller state, named for demo region)
-- ---------------------------------------------------------------------------
CREATE TABLE olist.warehouses (
    warehouse_id    SERIAL          NOT NULL,
    warehouse_code  VARCHAR(20)     NOT NULL,       -- e.g. 'WH-SE-001'
    region_label    VARCHAR(80),                    -- e.g. 'South East England'
    city            VARCHAR(80),
    state           CHAR(2),                        -- maps to Olist state code
    capacity_sqm    INTEGER,
    currency_code   CHAR(3)         NOT NULL DEFAULT 'GBP',
    country_code    CHAR(2)         NOT NULL DEFAULT 'GB',
    CONSTRAINT pk_warehouses PRIMARY KEY (warehouse_id)
);

CREATE UNIQUE INDEX ix_warehouses_code ON olist.warehouses (warehouse_code);
CREATE INDEX ix_warehouses_state ON olist.warehouses (state);

-- ---------------------------------------------------------------------------
-- PURCHASE_ORDERS  (synthetic — links IBM i ORDER_ITEMS.seller_id → EDB suppliers)
-- Represents the supplier-side operational view of fulfillment.
-- Each IBM i order item with a known seller gets a corresponding PO row here.
-- ---------------------------------------------------------------------------
CREATE TABLE olist.purchase_orders (
    po_id           SERIAL          NOT NULL,
    po_number       VARCHAR(20)     NOT NULL,       -- e.g. 'PO-2017-00001'
    order_id        CHAR(32)        NOT NULL,       -- FK ref to IBM i OLIST.ORDERS (cross-system)
    order_item_id   SMALLINT        NOT NULL,
    supplier_id     CHAR(32)        NOT NULL,
    warehouse_id    INTEGER,
    category_en     VARCHAR(80),                    -- English category (from translation CSV)
    unit_price      NUMERIC(10,2),
    freight_value   NUMERIC(10,2),
    ship_limit_date TIMESTAMP,
    po_status       VARCHAR(20)     NOT NULL DEFAULT 'FULFILLED',
    currency_code   CHAR(3)         NOT NULL DEFAULT 'GBP',
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_purchase_orders PRIMARY KEY (po_id),
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id)
        REFERENCES olist.suppliers (supplier_id) ON DELETE RESTRICT,
    CONSTRAINT fk_po_warehouse FOREIGN KEY (warehouse_id)
        REFERENCES olist.warehouses (warehouse_id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX ix_po_number   ON olist.purchase_orders (po_number);
CREATE INDEX ix_po_order_id        ON olist.purchase_orders (order_id);
CREATE INDEX ix_po_supplier        ON olist.purchase_orders (supplier_id);
CREATE INDEX ix_po_status_ship     ON olist.purchase_orders (po_status, ship_limit_date);

-- ---------------------------------------------------------------------------
-- Helpful view — joins POs back to suppliers + tier-2 for federated queries
-- Federated query in watsonx.data will join this view to IBM i OLIST.ORDERITEMS
-- The tier2_company_name / breach_status columns are the cyber demo payload —
-- they prove the tier-2 layer is visible here but absent from the IBM i ERP.
-- ---------------------------------------------------------------------------
CREATE VIEW olist.v_po_detail AS
SELECT
    po.po_id,
    po.po_number,
    po.order_id,
    po.order_item_id,
    po.category_en,
    po.unit_price,
    po.freight_value,
    po.ship_limit_date,
    po.po_status,
    po.currency_code,
    s.supplier_id,
    s.city               AS supplier_city,
    s.region_label       AS supplier_region,
    s.country_code,
    w.warehouse_code,
    w.region_label       AS warehouse_region,
    t2.company_name      AS tier2_company_name,
    t2.company_code      AS tier2_company_code,
    t2.service_type      AS tier2_service_type,
    t2.breach_status     AS tier2_breach_status,
    t2.cve_reference     AS tier2_cve_reference
FROM olist.purchase_orders po
JOIN olist.suppliers       s   ON s.supplier_id   = po.supplier_id
LEFT JOIN olist.warehouses w   ON w.warehouse_id  = po.warehouse_id
LEFT JOIN olist.tier2_suppliers t2 ON t2.tier2_id = s.subcontracted_to_id;
