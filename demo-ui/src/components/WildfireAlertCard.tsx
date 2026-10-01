/**
 * WildfireAlertCard.tsx — alert card for the eu-wildfire scenario.
 * Extracted from AlertCardsPanel.tsx.
 */

'use client'

import { Tag, SkeletonText } from '@carbon/react'
import { Warning, Misuse, ChartLineData, ArrowRight } from '@carbon/icons-react'
import type { AlertCard } from '../pages/api/alerts'
import { SeverityBadge, FieldRow } from './CyberAlertCard'

export function WildfireAlertCard({ card, isSecurity, isTechnical, isExecutive, isOperations }: {
  card: AlertCard; isSecurity?: boolean; isTechnical?: boolean; isExecutive?: boolean; isOperations?: boolean
}) {
  const a = card.alert as Record<string, unknown> | null
  const atRiskPos = (a?.at_risk_pos as Record<string, unknown>[] | undefined) ?? []
  const demandSpike = (a?.demand_spike as Record<string, unknown>[] | undefined) ?? []

  const enablementActions = isSecurity ? [
    'Route disruption feed → SIEM geo-correlation → immediate corridor risk scoring',
    'Auto-trigger SOAR: reroute freight, alert regional security, log chain of custody',
    'PowerSC: compliance posture maintained during physical disruption events',
  ] : isTechnical ? [
    'Route telemetry webhook → Kafka → Flink processor → federated Presto query → Iceberg sink',
    'Real-time POS stream joined to warehouse corridors — sub-second demand spike detection',
    'Iceberg ACID guarantees: consistent exposure view across concurrent reroute decisions',
  ] : isOperations ? [
    'Reroute 5 of 7 POs before business day starts — Alpine passes pre-approved.',
    'Demand spike on key SKUs detected in real-time POS — inventory rebalanced before stockout.',
    'On-call manager alerted via PagerDuty at 06:02 — decision by 06:15, action by 07:30.',
  ] : isExecutive ? [
    '90-minute response vs 4-day delay. £6.8K saved vs £8.7K cost. SLAs: 0 breaches.',
    'Freight continuity maintained despite physical corridor closure — no revenue loss.',
    'Workload mobility on Power: data stays accessible even when logistics corridors fail.',
  ] : [
    'Reroute 5 of 7 POs before business day starts — Alpine passes pre-approved.',
    'Demand spike on key SKUs detected in real-time POS — inventory rebalanced before stockout.',
    'On-call manager alerted via PagerDuty at 06:02 — decision by 06:15, action by 07:30.',
  ]

  return (
    <div className="alert-card-enter" style={{
      background: 'var(--demo-surface)',
      border: '1px solid var(--demo-orange)',
      borderTop: '3px solid var(--demo-orange)',
      borderRadius: 2,
      marginBottom: 12,
      overflow: 'hidden',
    }}>
      {/* Card header */}
      <div style={{
        padding: '10px 14px',
        background: '#2d1500',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        borderBottom: '1px solid var(--demo-orange)',
      }}>
        <Misuse size={18} style={{ color: 'var(--demo-orange)', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--demo-orange)', marginBottom: 2 }}>
            LOGISTICS DISRUPTION ALERT
          </div>
          <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>
            {card.signal.signal_code}
            {card.signal.temp_celsius != null && ` · ${card.signal.temp_celsius}°C`}
            {' · '}
            {new Date(card.firedAt).toLocaleTimeString('en-GB')}
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
        background: '#1f1600',
      }}>
        {card.signal.headline}
      </div>

      {/* AT_RISK_PO section */}
      {atRiskPos.length > 0 && (
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--demo-border)' }}>
          <div style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--demo-orange)',
            textTransform: 'uppercase',
            letterSpacing: '0.07em',
            marginBottom: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}>
            <Warning size={14} />
            At-Risk Purchase Orders ({atRiskPos.length})
          </div>
          {atRiskPos.map((po, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto auto auto',
              gap: 8,
              padding: '4px 0',
              borderBottom: '1px solid #2d2d2d',
              fontSize: 11,
              fontFamily: 'IBM Plex Mono, monospace',
              alignItems: 'center',
            }}>
              <span style={{ color: 'var(--demo-text)' }}>{String(po.po_number ?? '—')}</span>
              <span style={{ color: 'var(--demo-text-muted)' }}>{String(po.category_en ?? '—')}</span>
              <span style={{ color: 'var(--demo-orange)' }}>
                {po.order_value != null ? `£${Number(po.order_value).toFixed(0)}` : '—'}
              </span>
              <Tag type="red" size="sm">
                {po.days_to_ship_limit != null ? `${po.days_to_ship_limit}d` : '—'}
              </Tag>
            </div>
          ))}
        </div>
      )}

      {/* DEMAND_SPIKE section */}
      {demandSpike.length > 0 && (
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--demo-border)' }}>
          <div style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--demo-yellow)',
            textTransform: 'uppercase',
            letterSpacing: '0.07em',
            marginBottom: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}>
            <ChartLineData size={14} />
            Demand Spike SKUs ({demandSpike.length})
          </div>
          {demandSpike.map((ds, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto auto',
              gap: 8,
              padding: '4px 0',
              borderBottom: '1px solid #2d2d2d',
              fontSize: 11,
              fontFamily: 'IBM Plex Mono, monospace',
              alignItems: 'center',
            }}>
              <span style={{ color: 'var(--demo-text)' }}>{String(ds.sku_id ?? '—')}</span>
              <span style={{ color: 'var(--demo-text-muted)', fontSize: 10 }}>
                {String(ds.region ?? '—')} · {String(ds.units_last_hour ?? '—')} /hr
              </span>
              <Tag type={String(ds.stock_alert ?? '').includes('CRITICAL') ? 'red' : 'warm-gray'} size="sm">
                {String(ds.stock_alert ?? '').replace('CRITICAL — ', '⚠ ')}
              </Tag>
            </div>
          ))}
        </div>
      )}

      {/* Scalar fallback */}
      {atRiskPos.length === 0 && demandSpike.length === 0 && a && (
        <div style={{ padding: '10px 14px' }}>
          {Object.entries(a).map(([k, v]) => (
            <FieldRow key={k} label={k} value={String(v ?? '—')} />
          ))}
        </div>
      )}

      {a === null && <div style={{ padding: '12px 14px' }}><SkeletonText paragraph lineCount={4} /></div>}

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
          📡 Upstream: {card.signal.source_feed ?? 'Route & Travel Disruption Intelligence'}
        </span>
        <span className="source-badge badge-ibmi">IBM i · ORDERS + PRODUCTS</span>
        <span className="source-badge badge-edb">EDB · suppliers + warehouses</span>
        <span className="source-badge badge-iceberg">Iceberg · retail_signals + pos_events</span>
        {card.source === 'stub' && (
          <span className="source-badge" style={{ background: '#262626', border: '1px solid #525252', color: '#8d8d8d', marginLeft: 'auto' }}>
            ⚡ simulated injection
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

      {card.signal.detail_url && (
        <div style={{ padding: '6px 14px', borderTop: '1px solid var(--demo-border)', background: '#1a1a1a' }}>
          <a href={card.signal.detail_url} target="_blank" rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--demo-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
            Route Disruption Feed &amp; Incident Context <ArrowRight size={12} />
          </a>
        </div>
      )}
    </div>
  )
}
