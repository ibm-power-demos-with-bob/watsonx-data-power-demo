-- ============================================================================
-- Financial Services Demo Query: Real-Time Fraud Triage & Core Account Federation
-- Joins streaming transaction risk scores with Core Banking Ledgers on Db2 for IBM i.
-- ============================================================================

SELECT 
    t.transaction_id,
    t.account_id,
    acc.account_holder_name,
    acc.kyc_tier,
    acc.account_balance,
    t.amount,
    t.currency,
    t.channel,
    t.country_code,
    t.risk_score,
    CASE 
        WHEN t.risk_score >= 0.90 THEN 'AUTO-BLOCK & FREEZE CARD'
        WHEN t.risk_score >= 0.75 THEN 'PUSH STEP-UP AUTH / 2FA'
        ELSE 'ALLOW'
    END AS automated_decision
FROM 
    lakehouse.finance.transactions_stream t
-- In-Place Zero-Copy Federation with Db2 on IBM i (Core Banking Ledger)
JOIN 
    db2_ibmi.core_banking.accounts acc ON t.account_id = acc.account_id
WHERE 
    t.epoch_ms >= (to_unixtime(now()) * 1000) - (10 * 60 * 1000)
    AND t.is_flagged = TRUE
ORDER BY 
    t.risk_score DESC, t.amount DESC;
