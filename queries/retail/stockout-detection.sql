-- ============================================================================
-- Retail Demo Query 1: Real-Time Stockout Risk Detection
-- Aggregates live POS checkout streams to flag stores with rapid inventory depletion.
-- ============================================================================

SELECT 
    p.store_id,
    p.region,
    p.sku_id,
    SUM(p.quantity) AS units_sold_last_hour,
    ROUND(SUM(p.total_amount), 2) AS gross_sales,
    MIN(p.inventory_remaining_estimate) AS current_shelf_stock,
    CASE 
        WHEN MIN(p.inventory_remaining_estimate) <= 2 THEN 'CRITICAL - IMMEDIATE RESTOCK'
        WHEN MIN(p.inventory_remaining_estimate) <= 5 THEN 'HIGH RISK'
        ELSE 'NORMAL'
    END AS stockout_alert_level
FROM 
    lakehouse.retail.pos_stream p
WHERE 
    p.epoch_ms >= (to_unixtime(now()) * 1000) - (60 * 60 * 1000)
GROUP BY 
    p.store_id, p.region, p.sku_id
HAVING 
    MIN(p.inventory_remaining_estimate) <= 5
ORDER BY 
    current_shelf_stock ASC, units_sold_last_hour DESC;
