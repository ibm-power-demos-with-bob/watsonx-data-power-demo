-- ============================================================================
-- Telco Demo Query 1: Real-Time Network Degradation Detection
-- Engine: watsonx.data Presto C++ / Iceberg Lakehouse
-- ============================================================================
-- Detects cell towers experiencing severe packet loss and high latency
-- across the last 5 minutes of streaming telemetry.

SELECT 
    t.tower_id,
    t.region,
    COUNT(*) AS metric_samples,
    ROUND(AVG(t.latency_ms), 1) AS avg_latency_ms,
    ROUND(MAX(t.packet_loss_pct), 2) AS max_packet_loss_pct,
    ROUND(AVG(t.cpu_util_pct), 1) AS avg_cpu_util,
    SUM(CASE WHEN t.status = 'DEGRADED' THEN 1 ELSE 0 END) AS degraded_events
FROM 
    lakehouse.telco.live_network_metrics t
WHERE 
    t.epoch_ms >= (to_unixtime(now()) * 1000) - (5 * 60 * 1000)
GROUP BY 
    t.tower_id, t.region
HAVING 
    MAX(t.packet_loss_pct) > 2.0 OR AVG(t.latency_ms) > 150
ORDER BY 
    max_packet_loss_pct DESC, avg_latency_ms DESC
LIMIT 20;
