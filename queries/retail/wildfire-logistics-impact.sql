-- ============================================================================
-- Retail Demo Query 4: Wildfire Road Closure — Logistics Disruption Alert
-- ============================================================================
-- Triggered when the AI sidecar detects an ExternalSignalEvent with
-- signal_category = 'LOGISTICS_DISRUPTION' and severity IN ('HIGH','CRITICAL').
--
-- Reference scenario: European wildfires summer 2026 — record temperatures
-- cause fires across southern France and northern Spain, forcing closure of
-- the A9/AP-7 road corridor (the primary Lyon–Barcelona freight route).
-- This is SUDDEN and UNFORESEEABLE — unlike a heat forecast, nobody planned
-- for this specific fire on this specific road on this specific morning.
-- Source: Euronews, August 2026.
--   https://www.euronews.com/my-europe/2026/08/13/millions-across-europe-swelter-through-a-new-wave-of-extreme-temperatures
--
-- This query answers two questions the static report cannot:
--   1. Which open purchase orders are routed through the affected corridor
--      and at risk of missing their ship limit date?
--      (IBM i orders + EDB suppliers/warehouses — cross-system join)
--   2. Which product categories will see a demand spike in adjacent regions
--      as consumers stock up ahead of potential shortages?
--      (Iceberg live POS velocity — real-time signal)
--
-- Three-source federation:
--   IBM i (Db2)   — OLIST.ORDERS, OLIST.ORDERITEMS, OLIST.PRODUCTS
--   EDB Postgres  — olist.suppliers, olist.warehouses, olist.purchase_orders
--   Iceberg/COS   — retail_signals (injected event), retail_pos_events (live)
-- ============================================================================

-- Step 1: The wildfire / road closure signal
WITH disruption_signal AS (
    SELECT
        sig.signal_code,
        sig.headline,
        sig.temp_celsius,
        sig.affected_sector,
        sig.severity,
        sig.timestamp           AS signal_fired_at,
        sig.epoch_ms            AS signal_epoch_ms
    FROM
        iceberg_data2.retail.retail_signals     sig
    WHERE
        sig.signal_category = 'LOGISTICS_DISRUPTION'
        AND sig.severity    IN ('HIGH', 'CRITICAL')
    ORDER BY
        sig.epoch_ms DESC
    LIMIT 1
),

-- Step 2: At-risk POs — LOGISTICS sector, ship limit within 10 days
-- These are the POs that were on a road now closed or severely disrupted.
-- EDB holds the supplier and warehouse; IBM i holds the order and product.
at_risk_pos AS (
    SELECT
        po.po_number,
        po.order_id,
        po.order_item_id,
        po.ship_limit_date,
        po.currency_code,
        ROUND(po.unit_price + po.freight_value, 2)   AS order_value,
        po.category_en,
        sup.supplier_id,
        sup.city                                      AS supplier_city,
        sup.region_label                              AS supplier_region,
        sup.country_code,
        w.warehouse_code,
        w.region_label                                AS warehouse_region,
        -- Days until ship limit — urgency ranking
        DATE_DIFF('day',
            CURRENT_DATE,
            CAST(po.ship_limit_date AS DATE))         AS days_to_ship_limit,
        ord.STATUS                                    AS ibmi_order_status,
        ord.ESTDLV                                    AS estimated_delivery
    FROM
        pg_olist.olist.purchase_orders               po
    JOIN
        pg_olist.olist.suppliers                     sup
        ON sup.supplier_id = po.supplier_id
    LEFT JOIN
        pg_olist.olist.warehouses                    w
        ON w.warehouse_id  = po.warehouse_id
    -- Cross back to IBM i for live order status
    JOIN
        ibmi_olist.OLIST.ORDERS                       ord
        ON ord.ORDERID = po.order_id
    -- Cross back to IBM i PRODUCTS for sector classification
    JOIN (
        SELECT DISTINCT oi.ORDERID, oi.ITEMID, p.SECTOR
        FROM   ibmi_olist.OLIST.ORDERITEMS oi
        JOIN   ibmi_olist.OLIST.PRODUCTS   p  ON p.PRODID = oi.PRODID
    )                                                 prod_sector
        ON  prod_sector.ORDERID = po.order_id
        AND prod_sector.ITEMID  = po.order_item_id
    CROSS JOIN
        disruption_signal                             sig
    WHERE
        po.po_status NOT IN ('CANCELLED', 'FULFILLED')
        -- Ship limit within 10 days of signal — these are the urgent ones
        AND po.ship_limit_date <= DATE_ADD('day', 10,
                                    CAST(sig.signal_fired_at AS DATE))
        AND po.ship_limit_date >= CAST(sig.signal_fired_at AS DATE)
        -- Sector filter — LOGISTICS = freight/road-dependent categories
        AND prod_sector.SECTOR = sig.affected_sector
),

-- Step 3: Demand spike — products likely to sell faster after the disruption
-- Short-horizon supply shock (road closed) drives panic buying in adjacent
-- regions: HOME_GOODS (generators, fans), FOOD_BEVERAGE (bottled water,
-- non-perishables), TECHNOLOGY (battery packs, comms devices).
demand_spike AS (
    SELECT
        pos.sku_id,
        pos.region,
        p.CATEN                                            AS category_en,
        p.SECTOR,
        SUM(pos.quantity)                                  AS units_last_hour,
        MIN(pos.inventory_remaining_estimate)              AS current_stock,
        CASE
            WHEN MIN(pos.inventory_remaining_estimate) <= 3  THEN 'CRITICAL — STOCKOUT'
            WHEN MIN(pos.inventory_remaining_estimate) <= 10 THEN 'LOW STOCK'
            ELSE 'MONITOR'
        END                                                AS stock_alert
    FROM
        iceberg_data2.retail.retail_pos_events             pos
    JOIN
        ibmi_olist.OLIST.PRODUCTS                          p
        ON p.PRODID = pos.sku_id
    WHERE
        pos.epoch_ms >= (to_unixtime(NOW()) * 1000) - (60 * 60 * 1000)
        -- Sectors most sensitive to this type of disruption
        AND p.SECTOR IN ('HOME_GOODS', 'FOOD_BEVERAGE', 'TECHNOLOGY')
    GROUP BY
        pos.sku_id, pos.region, p.CATEN, p.SECTOR
    HAVING
        -- Only surface SKUs already running low under elevated velocity
        MIN(pos.inventory_remaining_estimate) <= 10
)

-- Step 4: Combined disruption impact — one result set, two impact types
-- Row type 'AT_RISK_PO'  → supply side: freight POs that can't move
-- Row type 'DEMAND_SPIKE' → demand side: products flying off shelves
SELECT
    'AT_RISK_PO'                                       AS impact_type,
    sig.signal_code,
    sig.headline,
    sig.temp_celsius,
    ar.supplier_region                                 AS region,
    ar.warehouse_region,
    ar.currency_code,
    ar.po_number,
    ar.order_value,
    ar.days_to_ship_limit,
    ar.ibmi_order_status,
    ar.category_en,
    NULL                                               AS sku_id,
    NULL                                               AS stock_alert,
    NULL                                               AS units_last_hour
FROM
    at_risk_pos     ar
CROSS JOIN
    disruption_signal sig

UNION ALL

SELECT
    'DEMAND_SPIKE'                                     AS impact_type,
    sig.signal_code,
    sig.headline,
    sig.temp_celsius,
    ds.region,
    NULL                                               AS warehouse_region,
    'GBP'                                              AS currency_code,
    NULL                                               AS po_number,
    NULL                                               AS order_value,
    NULL                                               AS days_to_ship_limit,
    NULL                                               AS ibmi_order_status,
    ds.category_en,
    ds.sku_id,
    ds.stock_alert,
    ds.units_last_hour
FROM
    demand_spike    ds
CROSS JOIN
    disruption_signal sig

ORDER BY
    impact_type,
    days_to_ship_limit ASC NULLS LAST,
    units_last_hour    DESC NULLS LAST;

-- ============================================================================
-- Expected dashboard output (illustrative):
--
-- Row 1:  impact_type=AT_RISK_PO
--         signal_code=EU_WILDFIRE_ROAD_CLOSURE_2026
--         supplier_region=South East England
--         po_number=PO-2017-00142
--         order_value=£840.00
--         days_to_ship_limit=3
--         ibmi_order_status=processing
--         category_en=furniture_decor
--
-- Row 2:  impact_type=DEMAND_SPIKE
--         region=EMEA-South
--         sku_id=SKU-ORGANIC-MILK-01
--         stock_alert=LOW STOCK
--         units_last_hour=312
--
-- Presenter: "This fire broke out at 6am.  By 7am the A9 was closed.
-- We have seven POs due this week that cannot move.  At the same time,
-- three SKUs in adjacent regions are already running low as consumers
-- react.  Your weekly freight report was printed last Friday.
-- It has no idea any of this happened."
-- ============================================================================
