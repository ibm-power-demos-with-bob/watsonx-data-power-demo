-- ============================================================================
-- Retail Demo Query 3: Supplier Cyber Incident — Tier-2 Visibility Alert
-- ============================================================================
-- Triggered when the AI sidecar detects an ExternalSignalEvent with
-- signal_category = 'CYBER_INCIDENT' and severity IN ('HIGH', 'CRITICAL').
--
-- Reference scenario: MOVEit Transfer zero-day (CVE-2023-34362), June 2023.
-- A SQL injection vulnerability in a managed file transfer tool hit thousands
-- of organisations across every sector globally — logistics, retail supply
-- chains, financial services, healthcare.  Zero advance warning.
-- CISA advisory: https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-187a
--
-- THE KEY NARRATIVE — why federation is essential here:
--
--   Tier-1 direct suppliers  → live in Source 1 (IBM i / core ERP)
--   Tier-2 sub-contractors   → live in Source 2 (EDB / operational DB) ONLY
--                              They do not exist in the IBM i at all.
--
--   The breach hit Nexaflow Logistics Ltd and three other tier-2 companies —
--   fictional, but structurally real in this schema.  Your procurement team
--   cannot see them.  Your ERP cannot see them.  They are in the gap.
--   watsonx.data joins across the gap.
--
--   The final column — erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'
--   — is not decoration.  It is the point of the entire demo.
--
-- Three-source federation:
--   IBM i (Db2)     — OLIST.ORDERS, OLIST.ORDERITEMS, OLIST.PRODUCTS
--   EDB Postgres    — olist.tier2_suppliers (COMPROMISED), olist.suppliers,
--                     olist.purchase_orders
--   Iceberg/COS     — retail_signals (the injected CYBER_INCIDENT event)
-- ============================================================================

-- Step 1: The cyber incident signal from Iceberg
WITH cyber_signal AS (
    SELECT
        sig.signal_code,
        sig.headline,
        sig.affected_sector,
        sig.severity,
        sig.timestamp       AS signal_fired_at,
        sig.epoch_ms        AS signal_epoch_ms
    FROM
        iceberg_data2.retail.retail_signals     sig
    WHERE
        sig.signal_category = 'CYBER_INCIDENT'
        AND sig.severity    IN ('HIGH', 'CRITICAL')
    ORDER BY
        sig.epoch_ms DESC
    LIMIT 1
),

-- Step 2: Compromised tier-2 companies (EDB only — invisible to IBM i)
-- These are the fictional sub-contractors pre-seeded as COMPROMISED.
-- breach_status is set by setup/8-load-edb-olist.py at load time.
-- In a live integration, this would be updated by a threat intel feed.
compromised_tier2 AS (
    SELECT
        t2.tier2_id,
        t2.company_name,
        t2.company_code,
        t2.service_type,
        t2.region_label     AS tier2_region,
        t2.breach_notified,
        t2.cve_reference
    FROM
        pg_olist.olist.tier2_suppliers     t2
    WHERE
        t2.breach_status = 'COMPROMISED'
),

-- Step 3: Direct suppliers (tier-1) whose sub-contractor is compromised
-- This is the join that crosses the tier-2 visibility gap.
-- The supplier knows their own tier-2 partner (subcontracted_to_id FK in EDB).
-- The IBM i ERP only knows the tier-1 supplier_id — nothing below it.
exposed_suppliers AS (
    SELECT
        s.supplier_id,
        s.city                  AS supplier_city,
        s.region_label          AS supplier_region,
        s.country_code,
        s.currency_code,
        ct2.company_name        AS tier2_company,
        ct2.service_type        AS tier2_service,
        ct2.tier2_region,
        ct2.breach_notified,
        ct2.cve_reference
    FROM
        pg_olist.olist.suppliers       s
    JOIN
        compromised_tier2               ct2
        ON ct2.tier2_id = s.subcontracted_to_id
),

-- Step 4: Open orders at risk — join IBM i orders to exposed EDB suppliers
-- This is the three-source join: Iceberg signal → EDB tier-2/suppliers → IBM i orders
at_risk_orders AS (
    SELECT
        po.po_number,
        po.order_id,
        po.order_item_id,
        po.ship_limit_date,
        po.currency_code,
        ROUND(po.unit_price + po.freight_value, 2)  AS order_value,
        po.category_en,
        es.supplier_id,
        es.supplier_city,
        es.supplier_region,
        es.country_code,
        es.tier2_company,
        es.tier2_service,
        es.tier2_region,
        es.breach_notified,
        es.cve_reference,
        ord.STATUS                                  AS ibmi_order_status,
        DATE_DIFF('day',
            CURRENT_DATE,
            CAST(po.ship_limit_date AS DATE))       AS days_to_ship_limit
    FROM
        pg_olist.olist.purchase_orders     po
    JOIN
        exposed_suppliers                   es
        ON es.supplier_id = po.supplier_id
    -- Cross back to IBM i for live order status — the second system join
    JOIN
        ibmi_olist.OLIST.ORDERS             ord
        ON ord.ORDERID = po.order_id
    WHERE
        po.po_status NOT IN ('CANCELLED', 'FULFILLED')
)

-- Step 5: Exposure summary — what the dashboard alert card shows
SELECT
    sig.signal_code,
    sig.headline,
    sig.severity,
    sig.signal_fired_at,

    -- Tier-2 breach detail (from EDB — not in IBM i)
    ar.tier2_company                                    AS compromised_tier2_company,
    ar.tier2_service                                    AS compromised_service_type,
    ar.tier2_region,
    ar.cve_reference,
    ar.breach_notified,

    -- Business impact (joins across IBM i + EDB)
    ar.supplier_region,
    ar.currency_code,
    COUNT(DISTINCT ar.po_number)                        AS open_po_count,
    COUNT(DISTINCT ar.supplier_id)                      AS tier1_suppliers_affected,
    ROUND(SUM(ar.order_value), 2)                       AS total_exposure,
    MIN(ar.ship_limit_date)                             AS earliest_ship_limit,
    COUNT(CASE
        WHEN ar.days_to_ship_limit BETWEEN 0 AND 7
        THEN 1
    END)                                                AS critical_pos_7_days,

    -- The punchline — literally in the result set
    'NOT VISIBLE IN ERP WITHOUT FEDERATION'             AS erp_visibility

FROM
    at_risk_orders  ar
CROSS JOIN
    cyber_signal    sig
GROUP BY
    sig.signal_code, sig.headline, sig.severity, sig.signal_fired_at,
    ar.tier2_company, ar.tier2_service, ar.tier2_region,
    ar.cve_reference, ar.breach_notified,
    ar.supplier_region, ar.currency_code
ORDER BY
    total_exposure DESC;

-- ============================================================================
-- Expected dashboard output (illustrative — one row per compromised tier-2):
--
-- signal_code                 : MOVEIT_STYLE_BREACH_LOGISTICS_2024
-- severity                    : CRITICAL
-- signal_fired_at             : 2024-06-06T09:14:00Z
--
-- compromised_tier2_company   : Nexaflow Logistics Ltd         ← fictional
-- compromised_service_type    : Managed File Transfer
-- tier2_region                : South East England
-- cve_reference               : CVE-2023-34362
-- breach_notified             : 2024-06-06 09:14:00
--
-- supplier_region             : South East England
-- currency_code               : GBP
-- open_po_count               : 14
-- tier1_suppliers_affected    : 6
-- total_exposure              : £47,230.00
-- earliest_ship_limit         : 2024-06-10
-- critical_pos_7_days         : 9
-- erp_visibility              : NOT VISIBLE IN ERP WITHOUT FEDERATION
--
-- Presenter script:
-- "Nexaflow Logistics Ltd.  Managed file transfer — the invisible layer
--  between your direct suppliers and their own freight network.
--  [pause]
--  Your ERP has never heard of them.  Look at that last column.
--  Nine purchase orders due this week.  £47,000 exposure.
--  We found this because watsonx.data joined across the gap.
--  Your static report cannot even ask this question —
--  because from where it sits, this company does not exist."
-- ============================================================================
