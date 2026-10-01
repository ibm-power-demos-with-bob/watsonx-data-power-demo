/**
 * CyberAlertCard.tsx — alert card for the supplier-cyber-incident scenario.
 * Extracted from AlertCardsPanel.tsx.
 */

'use client'

import { SkeletonText } from '@carbon/react'
import { Warning, ArrowRight } from '@carbon/icons-react'
import type { AlertCard } from '../pages/api/alerts'

export function SeverityBadge({ severity }: { severity: string }) {
  const cfg: Record<string, { color: string; label: string }> = {
    CRITICAL: { color: 'var(--demo-red)',    label: '🔴 CRITICAL' },
    HIGH:     { color: 'var(--demo-orange)', label: '🟠 HIGH' },
    MEDIUM:   { color: 'var(--demo-yellow)', label: '🟡 MEDIUM' },
    LOW:      { color: 'var(--demo-green)',  label: '🟢 LOW' },
  }
  const { color, label } = cfg[severity] ?? { color: '#aaa', label: severity }
  return (
    <span style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: '0.05em' }}>
      {label}
    </span>
  )
}

export function FieldRow({ label, value, highlight }: { label: string; value: React.ReactNode; highlight?: boolean }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '160px 1fr',
      gap: 8,
      padding: '4px 0',
      borderBottom: '1px solid #2d2d2d',
      fontSize: 12,
    }}>
      <span style={{ color: 'var(--demo-text-muted)', fontFamily: 'IBM Plex Mono, monospace', fontSize: 11 }}>
        {label}
      </span>
      <span style={{
        color: highlight ? 'var(--demo-red)' : 'var(--demo-text)',
        fontWeight: highlight ? 700 : 400,
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 11,
        wordBreak: 'break-word',
      }}>
        {value}
      </span>
    </div>
  )
}

export function CyberAlertCard({ card, isSecurity, isTechnical, isExecutive, isOperations }: {
  card: AlertCard; isSecurity?: boolean; isTechnical?: boolean; isExecutive?: boolean; isOperations?: boolean
}) {
  const a = card.alert as Record<string, unknown> | null

  const enablementActions = isSecurity ? [
    'Auto-enrich SIEM with tier-2 supplier graph → immediate blast radius assessment',
    'Trigger SOAR playbook: isolate affected POs, notify procurement, log evidence chain',
    'PowerSC continuous compliance scoring — audit trail auto-generated',
  ] : isTechnical ? [
    'Federated Presto query result → Kafka topic → downstream ML risk scoring pipeline',
    'Iceberg time-travel: query exposure state at any point during the breach window',
    'MMA on-box acceleration for real-time anomaly detection on supplier behavior',
  ] : isOperations ? [
    'Hold or re-route the affected POs before they ship — while the breach is still unfolding.',
    'Pre-qualify alternative suppliers with a full exposure list, in seconds not days.',
    'Notify procurement with the exact tier-2 companies your ERP has never heard of.',
  ] : isExecutive ? [
    'Contain £47K exposure in minutes — vs 80 hours with static reports.',
    'Zero SLA breaches. Zero emergency expediting costs. Board-ready audit trail.',
    'Single vendor accountability: IBM owns ERP, hardware, lakehouse, security.',
  ] : [
    'Hold or re-route the affected POs before they ship — while the breach is still unfolding.',
    'Pre-qualify alternative suppliers with a full exposure list, in seconds not days.',
    'Notify procurement with the exact tier-2 companies your ERP has never heard of.',
  ]

  return (
    <div className="alert-card-enter" style={{
      background: 'var(--demo-surface)',
      border: '1px solid var(--demo-red)',
      borderTop: '3px solid var(--demo-red)',
      borderRadius: 2,
      marginBottom: 12,
      overflow: 'hidden',
    }}>
      {/* Card header */}
      <div style={{
        padding: '10px 14px',
        background: '#2d0a0a',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        borderBottom: '1px solid var(--demo-red)',
      }}>
        <Warning size={18} style={{ color: 'var(--demo-red)', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--demo-red)', marginBottom: 2 }}>
            CYBER INCIDENT ALERT
          </div>
          <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>
            {card.signal.signal_code} · {new Date(card.firedAt).toLocaleTimeString('en-GB')}
          </div>
        </div>
        <SeverityBadge severity={card.signal.severity} />
      </div>

      {/* Signal headline */}
      <div style={{
        padding: '10px 14px',
        fontSize: 12,
        color: 'var(--demo-text-muted)',
        lineHeight: 1.6,
        borderBottom: '1px solid var(--demo-border)',
        background: '#1f1212',
      }}>
        {card.signal.headline}
      </div>

      {/* Query result fields */}
      <div style={{ padding: '10px 14px' }}>
        <div style={{
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--demo-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.07em',
          marginBottom: 8,
        }}>
          Federated Query Result — IBM i + EDB + Iceberg
        </div>
        {a ? (
          <>
            <FieldRow label="compromised_company" value={String(a.compromised_tier2_company ?? '—')} />
            <FieldRow label="service_type"        value={String(a.compromised_service_type ?? '—')} />
            <FieldRow label="tier2_region"        value={String(a.tier2_region ?? '—')} />
            <FieldRow label="cve_reference"       value={String(a.cve_reference ?? '—')} />
            <FieldRow label="currency"            value={String(a.currency_code ?? 'GBP')} />
            <FieldRow label="open_po_count"       value={String(a.open_po_count ?? '—')} />
            <FieldRow label="tier1_suppliers"     value={String(a.tier1_suppliers_affected ?? '—')} />
            <FieldRow
              label="total_exposure"
              value={a.total_exposure != null ? `£${Number(a.total_exposure).toLocaleString('en-GB', { minimumFractionDigits: 2 })}` : '—'}
            />
            <FieldRow label="critical_POs_7d"    value={String(a.critical_pos_7_days ?? '—')} />
            <FieldRow
              label="erp_visibility"
              value={String(a.erp_visibility ?? '—')}
              highlight={String(a.erp_visibility ?? '').includes('NOT VISIBLE')}
            />
          </>
        ) : (
          <SkeletonText paragraph lineCount={5} />
        )}
      </div>

      {/* ERP Visibility Punchline Badge */}
      {a && String(a.erp_visibility ?? '').includes('NOT VISIBLE') && (
        <div style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--demo-border)',
          background: '#2d0a0a',
          borderLeft: '4px solid var(--demo-red)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <Warning size={16} style={{ color: 'var(--demo-red)', flexShrink: 0 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--demo-red)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              KEY PUNCHLINE
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#ffb3b8', fontWeight: 600, fontFamily: 'IBM Plex Mono, monospace' }}>
            {String(a.erp_visibility)}
          </div>
          <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginTop: 4 }}>
            Your ERP has zero visibility of this tier-2 supplier. Federation is the only way to see this exposure.
          </div>
        </div>
      )}

      {/* Source chips */}
      <div style={{
        padding: '8px 14px',
        borderTop: '1px solid var(--demo-border)',
        display: 'flex',
        gap: 6,
        background: 'var(--demo-surface)',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}>
        <span className="source-badge" style={{ background: '#393939', color: '#f4f4f4', border: '1px solid #525252' }}>
          📡 Upstream: {card.signal.source_feed ?? 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)'}
        </span>
        <span className="source-badge badge-ibmi">IBM i · ORDERS</span>
        <span className="source-badge badge-edb">EDB · tier2_suppliers</span>
        <span className="source-badge badge-iceberg">Iceberg · retail_signals</span>
        {card.source === 'stub' && (
          <span className="source-badge" style={{ background: '#262626', border: '1px solid #525252', color: '#8d8d8d', marginLeft: 'auto' }}>
            ⚡ simulated injection
          </span>
        )}
        {card.source === 'live' && (
          <span className="source-badge" style={{ background: '#0a2a0a', border: '1px solid var(--demo-green)', color: 'var(--demo-green)', marginLeft: 'auto' }}>
            ✅ live federation query
          </span>
        )}
      </div>

      {/* What this enables */}
      <div style={{
        padding: '10px 14px',
        borderTop: '1px solid var(--demo-border)',
        background: '#0a1f0e',
        borderLeft: '3px solid var(--demo-green)',
      }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--demo-green)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
          What this enables {isSecurity && '(SEC)'} {isTechnical && '(TECH)'} {isOperations && '(OPS)'} {isExecutive && '(EXEC)'}
        </div>
        {enablementActions.map((action, i) => (
          <div key={i} style={{ display: 'flex', gap: 7, fontSize: 11, color: 'var(--demo-text-muted)', marginBottom: 4, lineHeight: 1.4 }}>
            <span style={{ color: 'var(--demo-green)', fontWeight: 700, flexShrink: 0 }}>✓</span>
            {action}
          </div>
        ))}
      </div>

      {/* Reference link */}
      {card.signal.detail_url && (
        <div style={{ padding: '6px 14px', borderTop: '1px solid var(--demo-border)', background: '#1a1a1a' }}>
          <a href={card.signal.detail_url} target="_blank" rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--demo-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
            Cybersecurity Vulnerability &amp; Threat Advisory <ArrowRight size={12} />
          </a>
        </div>
      )}
    </div>
  )
}
