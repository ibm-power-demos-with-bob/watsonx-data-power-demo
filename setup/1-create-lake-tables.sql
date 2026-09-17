-- ============================================================================
-- 1. Create Apache Iceberg Tables in watsonx.data Lakehouse
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS lakehouse.telco
WITH (location = 's3a://iceberg-bucket/telco/');

CREATE TABLE IF NOT EXISTS lakehouse.telco.live_network_metrics (
    event_id VARCHAR,
    event_type VARCHAR,
    timestamp VARCHAR,
    epoch_ms BIGINT,
    tower_id VARCHAR,
    region VARCHAR,
    signal_strength_dbm DOUBLE,
    latency_ms INTEGER,
    packet_loss_pct DOUBLE,
    active_users INTEGER,
    cpu_util_pct DOUBLE,
    status VARCHAR
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['region']
);

CREATE SCHEMA IF NOT EXISTS lakehouse.retail
WITH (location = 's3a://iceberg-bucket/retail/');

CREATE TABLE IF NOT EXISTS lakehouse.retail.pos_stream (
    event_id VARCHAR,
    event_type VARCHAR,
    timestamp VARCHAR,
    epoch_ms BIGINT,
    transaction_id VARCHAR,
    store_id VARCHAR,
    region VARCHAR,
    sku_id VARCHAR,
    quantity INTEGER,
    unit_price DOUBLE,
    total_amount DOUBLE,
    payment_method VARCHAR,
    inventory_remaining_estimate INTEGER
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['region']
);
