-- ============================================================================
-- Healthcare Demo Query: Real-Time Patient Flow & Bed Capacity Bottlenecks
-- Joins emergency triage flow with Clinical Staffing Rotas on AIX/Oracle.
-- ============================================================================

SELECT 
    p.facility_id,
    p.department,
    COUNT(*) AS total_recent_admissions,
    SUM(CASE WHEN p.acuity_level = 1 THEN 1 ELSE 0 END) AS critical_patients_count,
    ROUND(AVG(p.wait_time_minutes), 0) AS avg_wait_time_mins,
    ROUND(MAX(p.bed_occupancy_pct), 1) AS max_bed_occupancy_pct,
    rot.on_duty_nurses,
    rot.on_duty_physicians,
    CASE 
        WHEN MAX(p.bed_occupancy_pct) >= 95.0 THEN 'RED ALERT: DIVERT ADMISSIONS'
        WHEN MAX(p.bed_occupancy_pct) >= 85.0 THEN 'AMBER: CALL ON-CALL STAFF'
        ELSE 'GREEN: NORMAL OPERATIONS'
    END AS operational_status
FROM 
    lakehouse.healthcare.patient_admissions p
-- Federated join to Clinical Staffing Rostering on AIX
LEFT JOIN 
    oracle_aix.hospital_ops.staffing_roster rot 
    ON p.facility_id = rot.facility_id AND p.department = rot.department
WHERE 
    p.epoch_ms >= (to_unixtime(now()) * 1000) - (30 * 60 * 1000)
GROUP BY 
    p.facility_id, p.department, rot.on_duty_nurses, rot.on_duty_physicians
ORDER BY 
    max_bed_occupancy_pct DESC, critical_patients_count DESC;
