-- ============================================================================
-- Retail Demo Query 2: In-Place Cross-System Supply Chain Federation
-- Joins real-time POS checkouts with ERP Warehouse Stock on Db2 for IBM i
-- and Supplier Procurement Purchase Orders on Oracle on AIX.
-- ============================================================================

SELECT 
    pos.sku_id,
    prod.product_name,
    prod.category,
    SUM(pos.quantity) AS live_velocity_units,
    wh.central_warehouse_stock,
    wh.safety_threshold,
    po.vendor_name,
    po.po_number,
    po.expected_delivery_date,
    CASE 
        WHEN wh.central_warehouse_stock < wh.safety_threshold AND po.po_number IS NULL THEN 'TRIGGER AUTO-PO REORDER'
        WHEN wh.central_warehouse_stock < wh.safety_threshold THEN 'IN TRANSIT'
        ELSE 'OPTIMAL'
    END AS supply_action
FROM 
    lakehouse.retail.pos_stream pos
-- Federated join to Db2 on IBM i (Core Enterprise Master & Warehouse Catalog)
JOIN 
    db2_ibmi.erp.products prod ON pos.sku_id = prod.sku_id
JOIN 
    db2_ibmi.erp.warehouse_inventory wh ON pos.sku_id = wh.sku_id
-- Federated join to Oracle on AIX (Procurement & Supplier Commitments)
LEFT JOIN 
    oracle_aix.supply_chain.purchase_orders po 
    ON pos.sku_id = po.sku_id AND po.status = 'PENDING_DELIVERY'
WHERE 
    pos.epoch_ms >= (to_unixtime(now()) * 1000) - (2 * 60 * 60 * 1000)
GROUP BY 
    pos.sku_id, prod.product_name, prod.category, wh.central_warehouse_stock, 
    wh.safety_threshold, po.vendor_name, po.po_number, po.expected_delivery_date
ORDER BY 
    live_velocity_units DESC;
