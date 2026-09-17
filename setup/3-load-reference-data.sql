-- ============================================================================
-- 3. Load Sample Reference & Seed Data
-- ============================================================================

-- Simulating mock tables for local standalone demo runs if remote databases are not connected

CREATE SCHEMA IF NOT EXISTS db2_ibmi.telecom_core;

CREATE TABLE IF NOT EXISTS db2_ibmi.telecom_core.tower_infrastructure (
    tower_id VARCHAR,
    hardware_vendor VARCHAR,
    firmware_version VARCHAR,
    power_consumption_kwh DOUBLE,
    installation_year INTEGER
);

INSERT INTO db2_ibmi.telecom_core.tower_infrastructure VALUES
('TWR-LON-001', 'Ericsson', 'v14.2.1', 4.2, 2022),
('TWR-LON-002', 'Nokia', 'v9.8.0', 3.8, 2021),
('TWR-MID-001', 'Ericsson', 'v14.1.9', 4.1, 2020),
('TWR-MAN-001', 'Huawei Legacy', 'v8.1.0', 5.6, 2018),
('TWR-SCO-001', 'Nokia', 'v10.1.2', 3.4, 2023);

CREATE SCHEMA IF NOT EXISTS oracle_aix.servicedesk;

CREATE TABLE IF NOT EXISTS oracle_aix.servicedesk.incident_tickets (
    ticket_id VARCHAR,
    asset_id VARCHAR,
    ticket_status VARCHAR,
    severity VARCHAR,
    sla_breach_risk VARCHAR,
    opened_timestamp VARCHAR
);

INSERT INTO oracle_aix.servicedesk.incident_tickets VALUES
('INC-99012', 'TWR-LON-001', 'OPEN', 'CRITICAL', 'HIGH', '2026-03-29T10:00:00Z'),
('INC-99018', 'TWR-MAN-001', 'OPEN', 'HIGH', 'MEDIUM', '2026-03-29T11:15:00Z');
