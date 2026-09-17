-- ============================================================================
-- Telco Demo Query 2: In-Place Cross-System Federation
-- Joins real-time lakehouse telemetry with CRM Ticketing on Oracle on AIX
-- and Infrastructure Asset Inventory on Db2 for IBM i.
-- ============================================================================
-- NO DATA MOVEMENT: Federated in real-time across IBM Power LPARs.

SELECT 
    l.tower_id,
    l.region,
    ast.hardware_vendor,
    ast.firmware_version,
    ast.power_consumption_kwh,
    ROUND(AVG(l.latency_ms), 1) AS live_avg_latency,
    ROUND(MAX(l.packet_loss_pct), 2) AS peak_loss_pct,
    COUNT(DISTINCT crm.ticket_id) AS open_incident_tickets,
    MAX(crm.sla_breach_risk) AS highest_sla_risk
FROM 
    lakehouse.telco.live_network_metrics l
-- Federated join to Oracle on AIX (CRM & Incident Tickets)
LEFT JOIN 
    oracle_aix.servicedesk.incident_tickets crm 
    ON l.tower_id = crm.asset_id AND crm.ticket_status = 'OPEN'
-- Federated join to Db2 on IBM i (Core Enterprise Asset Register)
LEFT JOIN 
    db2_ibmi.telecom_core.tower_infrastructure ast 
    ON l.tower_id = ast.tower_id
WHERE 
    l.epoch_ms >= (to_unixtime(now()) * 1000) - (15 * 60 * 1000)
GROUP BY 
    l.tower_id, l.region, ast.hardware_vendor, ast.firmware_version, ast.power_consumption_kwh
HAVING 
    MAX(l.packet_loss_pct) > 1.5 OR COUNT(DISTINCT crm.ticket_id) > 0
ORDER BY 
    open_incident_tickets DESC, peak_loss_pct DESC;
