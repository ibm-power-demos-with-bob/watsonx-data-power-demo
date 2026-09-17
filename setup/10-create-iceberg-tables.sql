-- ============================================================================
-- Step 10: Create Iceberg tables in watsonx.data
-- ============================================================================
-- Run these statements ONCE in the watsonx.data Query workspace (or via the
-- REST API query endpoint) before starting setup/6-pos-to-iceberg.py.
--
-- These tables are the Iceberg/COS Source 3 in the three-source federation:
--
--   retail_pos_events  — live POS stream written by 6-pos-to-iceberg.py
--   retail_signals     — injected cyber/wildfire events (also written by
--                        6-pos-to-iceberg.py --with-signals)
--
-- The tables are Hive-partitioned by dt (date) so Presto can prune partitions
-- efficiently. The writer creates files at:
--   <bucket>/iceberg_data2/retail/<table>/dt=YYYY-MM-DD/<uuid>.parquet
--
-- Prerequisites
-- -------------
--   1. watsonx.data Presto engine (presto-demo) is Running
--   2. Iceberg catalog (iceberg_data2) is associated with presto-demo
--   3. setup/4-provision-via-rest-api.py has been run (creates catalog + COS)
-- ============================================================================

-- Create the retail schema inside the Iceberg catalog
CREATE SCHEMA IF NOT EXISTS iceberg_data2.retail
WITH (location = 's3a://watsonx-data-a29df4cf-abfc-4907-a79c-59223d766db9/iceberg_data2/retail/');

-- ============================================================================
-- Table 1: retail_pos_events
-- Live POS transaction stream — written continuously by 6-pos-to-iceberg.py
-- Used by wildfire-logistics-impact.sql (demand_spike CTE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS iceberg_data2.retail.retail_pos_events (
    event_id                     VARCHAR,
    event_type                   VARCHAR,
    timestamp                    VARCHAR,      -- ISO-8601 string from the generator
    epoch_ms                     BIGINT,       -- milliseconds since epoch — used for time-window filter
    transaction_id               VARCHAR,
    store_id                     VARCHAR,
    region                       VARCHAR,
    sku_id                       VARCHAR,
    sector                       VARCHAR,
    quantity                     INTEGER,
    unit_price                   DOUBLE,
    total_amount                 DOUBLE,
    payment_method               VARCHAR,
    inventory_remaining_estimate INTEGER,
    dt                           VARCHAR       -- partition column: YYYY-MM-DD
)
WITH (
    format           = 'PARQUET',
    partitioning     = ARRAY['dt'],
    location         = 's3a://watsonx-data-a29df4cf-abfc-4907-a79c-59223d766db9/iceberg_data2/retail/retail_pos_events/'
);

-- ============================================================================
-- Table 2: retail_signals
-- Injected signal events (cyber incident, logistics disruption)
-- Used by both cyber-supplier-incident.sql and wildfire-logistics-impact.sql
-- ============================================================================
CREATE TABLE IF NOT EXISTS iceberg_data2.retail.retail_signals (
    event_id         VARCHAR,
    event_type       VARCHAR,
    timestamp        VARCHAR,      -- ISO-8601 string
    epoch_ms         BIGINT,       -- used for ORDER BY epoch_ms DESC LIMIT 1
    signal_category  VARCHAR,      -- CYBER_INCIDENT | LOGISTICS_DISRUPTION
    signal_code      VARCHAR,      -- e.g. MOVEIT_STYLE_BREACH_LOGISTICS_2024
    affected_sector  VARCHAR,      -- LOGISTICS | TECHNOLOGY | etc.
    severity         VARCHAR,      -- LOW | MEDIUM | HIGH | CRITICAL
    headline         VARCHAR,      -- human-readable summary shown on alert card
    detail_url       VARCHAR,      -- reference URL
    temp_celsius     DOUBLE,       -- populated for WEATHER_EVENT / wildfire
    ticker_symbol    VARCHAR,      -- populated for MARKET_EVENT signals
    price_change_pct DOUBLE,       -- populated for MARKET_EVENT signals
    injected         BOOLEAN,      -- true = synthetic injection for demo
    source_feed      VARCHAR,      -- e.g. "CISA KEV / X-Force Exchange"
    source_channel   VARCHAR,      -- e.g. "Global Cyber Threat Intelligence"
    dt               VARCHAR       -- partition column: YYYY-MM-DD
)
WITH (
    format           = 'PARQUET',
    partitioning     = ARRAY['dt'],
    location         = 's3a://watsonx-data-a29df4cf-abfc-4907-a79c-59223d766db9/iceberg_data2/retail/retail_signals/'
);

-- ============================================================================
-- Verify
-- ============================================================================
SHOW TABLES IN iceberg_data2.retail;
-- Expected: retail_pos_events, retail_signals

-- After running setup/6-pos-to-iceberg.py --once:
SELECT COUNT(*) FROM iceberg_data2.retail.retail_pos_events;
-- Expected: 20 (one batch of CONFIG batch_size=20)

-- After injecting a signal via the demo UI and running with --with-signals:
SELECT signal_category, signal_code, severity, timestamp
FROM   iceberg_data2.retail.retail_signals
ORDER BY epoch_ms DESC
LIMIT  5;
