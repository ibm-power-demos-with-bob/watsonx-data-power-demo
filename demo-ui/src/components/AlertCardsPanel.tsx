/**
 * AlertCardsPanel
 *
 * Renders the federated query result alert cards.
 * Two card types, matching the two demo arc scenarios:
 *
 *   CyberAlertCard    — supplier-cyber-incident
 *   WildfireAlertCard — eu-wildfire
 *
 * The "NOT VISIBLE IN ERP WITHOUT FEDERATION" punchline is rendered
 * prominently on the cyber card.  The wildfire card surfaces both
 * AT_RISK_PO rows and DEMAND_SPIKE rows.
 *
 * Cards slide in as new signals fire.  The panel polls GET /api/alerts
 * on mount and accepts live pushes from the parent via `alerts` prop.
 */

'use client'

import { useEffect, useState } from 'react'
import {
  Tag,
  Button,
  SkeletonText,
} from '@carbon/react'
import { Warning, Misuse, ChartLineData, ArrowRight } from '@carbon/icons-react'
import type { AlertCard } from '../pages/api/alerts'

interface Props {
  alerts: AlertCard[]
  loading?: boolean
}

function SeverityBadge({ severity }: { severity: string }) {
  const cfg: Record<string, { color: string; label: string }> = {
    CRITICAL: { color: 'var(--demo-red)',    label: '🔴 CRITICAL' },
    HIGH:     { color: 'var(--demo-orange)', label: '🟠 HIGH' },
    MEDIUM:   { color: 'var(--demo-yellow)', label: '🟡 MEDIUM' },
    LOW:      { color: 'var(--demo-green)',  label: '🟢 LOW' },
  }
  const { color, label } = cfg[severity] ?? { color: '#aaa', label: severity }
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 700,
        color,
        letterSpacing: '0.05em',
      }}
    >
      {label}
    </span>
  )
}

function FieldRow({ label, value, highlight }: { label: string; value: React.ReactNode; highlight?: boolean }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '160px 1fr',
        gap: 8,
        padding: '4px 0',
        borderBottom: '1px solid #2d2d2d',
        fontSize: 12,
      }}
    >
      <span style={{ color: 'var(--demo-text-muted)', fontFamily: 'IBM Plex Mono, monospace', fontSize: 11 }}>
        {label}
      </span>
      <span
        style={{
          color: highlight ? 'var(--demo-red)' : 'var(--demo-text)',
          fontWeight: highlight ? 700 : 400,
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 11,
          wordBreak: 'break-word',
        }}
      >
        {value}
      </span>
    </div>
  )
}

function CyberAlertCard({ card }: { card: AlertCard }) {
  const a = card.alert as Record<string, unknown> | null
  return (
    <div
      className="alert-card-enter"
      style={{
        background: 'var(--demo-surface)',
        border: '1px solid var(--demo-red)',
        borderTop: '3px solid var(--demo-red)',
        borderRadius: 2,
        marginBottom: 12,
        overflow: 'hidden',
      }}
    >
      {/* Card header */}
      <div
        style={{
          padding: '10px 14px',
          background: '#2d0a0a',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          borderBottom: '1px solid var(--demo-red)',
        }}
      >
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
      <div
        style={{
          padding: '10px 14px',
          fontSize: 12,
          color: 'var(--demo-text-muted)',
          lineHeight: 1.6,
          borderBottom: '1px solid var(--demo-border)',
          background: '#1f1212',
        }}
      >
        {card.signal.headline}
      </div>

      {/* Query result fields */}
      <div style={{ padding: '10px 14px' }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--demo-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.07em',
            marginBottom: 8,
          }}
        >
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
              highlight={
                String(a.erp_visibility ?? '').includes('NOT VISIBLE')
              }
            />
          </>
        ) : (
          <SkeletonText paragraph lineCount={5} />
        )}
      </div>

      {/* Source chips */}
      <div
        style={{
          padding: '8px 14px',
          borderTop: '1px solid var(--demo-border)',
          display: 'flex',
          gap: 6,
          background: 'var(--demo-surface)',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <span className="source-badge" style={{ background: '#393939', color: '#f4f4f4', border: '1px solid #525252' }}>
          📡 Upstream: {card.signal.source_feed ?? 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)'}
        </span>
        <span className="source-badge badge-ibmi">IBM i · ORDERS</span>
        <span className="source-badge badge-edb">EDB · tier2_suppliers</span>
        <span className="source-badge badge-iceberg">Iceberg · retail_signals</span>
        {card.source === 'stub' && (
          <span
            className="source-badge"
            style={{ background: '#262626', border: '1px solid #525252', color: '#8d8d8d', marginLeft: 'auto' }}
          >
            ⚡ simulated injection
          </span>
        )}
      </div>

      {/* What this enables — the bridge beat before the outcome page */}
      <div
        style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--demo-border)',
          background: '#0a1f0e',
          borderLeft: '3px solid var(--demo-green)',
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--demo-green)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
          What this enables
        </div>
        {[
          'Hold or re-route the affected POs before they ship — while the breach is still unfolding.',
          'Pre-qualify alternative suppliers with a full exposure list, in seconds not days.',
          'Notify procurement with the exact tier-2 companies your ERP has never heard of.',
        ].map((action, i) => (
          <div key={i} style={{ display: 'flex', gap: 7, fontSize: 11, color: 'var(--demo-text-muted)', marginBottom: 4, lineHeight: 1.4 }}>
            <span style={{ color: 'var(--demo-green)', fontWeight: 700, flexShrink: 0 }}>✓</span>
            {action}
          </div>
        ))}
      </div>

      {/* Reference link */}
      {card.signal.detail_url && (
        <div style={{ padding: '6px 14px', borderTop: '1px solid var(--demo-border)', background: '#1a1a1a' }}>
          <a
            href={card.signal.detail_url}
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--demo-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            Cybersecurity Vulnerability &amp; Threat Advisory <ArrowRight size={12} />
          </a>
        </div>
      )}
    </div>
  )
}

function WildfireAlertCard({ card }: { card: AlertCard }) {
  const a = card.alert as Record<string, unknown> | null
  const atRiskPos = (a?.at_risk_pos as Record<string, unknown>[] | undefined) ?? []
  const demandSpike = (a?.demand_spike as Record<string, unknown>[] | undefined) ?? []

  return (
    <div
      className="alert-card-enter"
      style={{
        background: 'var(--demo-surface)',
        border: '1px solid var(--demo-orange)',
        borderTop: '3px solid var(--demo-orange)',
        borderRadius: 2,
        marginBottom: 12,
        overflow: 'hidden',
      }}
    >
      {/* Card header */}
      <div
        style={{
          padding: '10px 14px',
          background: '#2d1500',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          borderBottom: '1px solid var(--demo-orange)',
        }}
      >
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
      <div
        style={{
          padding: '10px 14px',
          fontSize: 12,
          color: 'var(--demo-text-muted)',
          lineHeight: 1.6,
          borderBottom: '1px solid var(--demo-border)',
          background: '#1f1600',
        }}
      >
        {card.signal.headline}
      </div>

      {/* AT_RISK_PO section */}
      {atRiskPos.length > 0 && (
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--demo-border)' }}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--demo-orange)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              marginBottom: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Warning size={14} />
            At-Risk Purchase Orders ({atRiskPos.length})
          </div>
          {atRiskPos.map((po, i) => (
            <div
              key={i}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto auto auto',
                gap: 8,
                padding: '4px 0',
                borderBottom: '1px solid #2d2d2d',
                fontSize: 11,
                fontFamily: 'IBM Plex Mono, monospace',
                alignItems: 'center',
              }}
            >
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
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--demo-yellow)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              marginBottom: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <ChartLineData size={14} />
            Demand Spike SKUs ({demandSpike.length})
          </div>
          {demandSpike.map((ds, i) => (
            <div
              key={i}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto auto',
                gap: 8,
                padding: '4px 0',
                borderBottom: '1px solid #2d2d2d',
                fontSize: 11,
                fontFamily: 'IBM Plex Mono, monospace',
                alignItems: 'center',
              }}
            >
              <span style={{ color: 'var(--demo-text)' }}>{String(ds.sku_id ?? '—')}</span>
              <span style={{ color: 'var(--demo-text-muted)', fontSize: 10 }}>
                {String(ds.region ?? '—')} · {String(ds.units_last_hour ?? '—')} /hr
              </span>
              <Tag
                type={
                  String(ds.stock_alert ?? '').includes('CRITICAL') ? 'red' : 'warm-gray'
                }
                size="sm"
              >
                {String(ds.stock_alert ?? '').replace('CRITICAL — ', '⚠ ')}
              </Tag>
            </div>
          ))}
        </div>
      )}

      {/* Scalar fallback when no structured data available */}
      {atRiskPos.length === 0 && demandSpike.length === 0 && a && (
        <div style={{ padding: '10px 14px' }}>
          {Object.entries(a).map(([k, v]) => (
            <FieldRow key={k} label={k} value={String(v ?? '—')} />
          ))}
        </div>
      )}

      {a === null && <div style={{ padding: '12px 14px' }}><SkeletonText paragraph lineCount={4} /></div>}

      {/* Source chips */}
      <div
        style={{
          padding: '8px 14px',
          borderTop: '1px solid var(--demo-border)',
          display: 'flex',
          gap: 6,
          background: 'var(--demo-surface)',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <span className="source-badge" style={{ background: '#393939', color: '#f4f4f4', border: '1px solid #525252' }}>
          📡 Upstream: {card.signal.source_feed ?? 'Route & Travel Disruption Intelligence'}
        </span>
        <span className="source-badge badge-ibmi">IBM i · ORDERS + PRODUCTS</span>
        <span className="source-badge badge-edb">EDB · suppliers + warehouses</span>
        <span className="source-badge badge-iceberg">Iceberg · retail_signals + pos_events</span>
        {card.source === 'stub' && (
          <span
            className="source-badge"
            style={{ background: '#262626', border: '1px solid #525252', color: '#8d8d8d', marginLeft: 'auto' }}
          >
            ⚡ simulated injection
          </span>
        )}
      </div>

      {/* What this enables — the bridge beat before the outcome page */}
      <div
        style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--demo-border)',
          background: '#0a1f0e',
          borderLeft: '3px solid var(--demo-green)',
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--demo-green)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
          What this enables
        </div>
        {[
          'Contact the carrier and place a hold on at-risk POs before the road closure causes a missed ship limit.',
          'Pre-approve rerouting via alternate corridors — before the business day even starts.',
          'Stock at-risk SKUs from adjacent warehouses using the live demand spike data already in the stream.',
        ].map((action, i) => (
          <div key={i} style={{ display: 'flex', gap: 7, fontSize: 11, color: 'var(--demo-text-muted)', marginBottom: 4, lineHeight: 1.4 }}>
            <span style={{ color: 'var(--demo-green)', fontWeight: 700, flexShrink: 0 }}>✓</span>
            {action}
          </div>
        ))}
      </div>

      {card.signal.detail_url && (
        <div style={{ padding: '6px 14px', borderTop: '1px solid var(--demo-border)', background: '#1a1a1a' }}>
          <a
            href={card.signal.detail_url}
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 11, color: 'var(--demo-blue)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            Route Disruption Feed &amp; Incident Context <ArrowRight size={12} />
          </a>
        </div>
      )}
    </div>
  )
}

export default function AlertCardsPanel({ alerts, loading }: Props) {
  const [localAlerts, setLocalAlerts] = useState<AlertCard[]>([])

  // Merge prop-pushed alerts (from signal injection) with any polled ones
  useEffect(() => {
    setLocalAlerts(alerts)
  }, [alerts])

  const displayed = localAlerts.length > 0 ? localAlerts : []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div
        style={{
          padding: '12px 16px 10px',
          borderBottom: '1px solid var(--demo-border)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <Warning size={16} style={{ color: 'var(--demo-red)' }} />
        <span style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.02em', flex: 1 }}>
          SIDECAR ALERTS
        </span>
        {displayed.length > 0 && (
          <span
            style={{
              background: 'var(--demo-red)',
              color: '#fff',
              borderRadius: 8,
              fontSize: 10,
              fontWeight: 700,
              padding: '1px 7px',
              minWidth: 20,
              textAlign: 'center',
            }}
          >
            {displayed.length}
          </span>
        )}
      </div>

      {/* Source label */}
      <div
        style={{
          padding: '6px 16px',
          borderBottom: '1px solid var(--demo-border)',
          display: 'flex',
          gap: 6,
          flexShrink: 0,
          background: 'var(--demo-surface)',
        }}
      >
        <span className="source-badge badge-ibmi">IBM i</span>
        <span className="source-badge badge-edb">EDB Postgres</span>
        <span className="source-badge badge-iceberg">Iceberg</span>
        <span style={{ fontSize: 11, color: 'var(--demo-text-muted)', alignSelf: 'center', marginLeft: 4 }}>
          Federated · 3-source join
        </span>
      </div>

      {/* Card list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px',
        }}
      >
        {loading && displayed.length === 0 && (
          <SkeletonText paragraph lineCount={6} />
        )}

        {!loading && displayed.length === 0 && (
          <div
            style={{
              textAlign: 'center',
              padding: '32px 16px',
              color: 'var(--demo-text-muted)',
              fontSize: 12,
              lineHeight: 1.7,
            }}
          >
            <Warning size={24} style={{ color: 'var(--demo-border)', marginBottom: 12 }} />
            <br />
            No alerts yet.
            <br />
            Use the Signal Injection panel to inject a scenario.
          </div>
        )}

        {displayed.slice().reverse().map((card) =>
          card.scenario === 'supplier-cyber-incident' ? (
            <CyberAlertCard key={card.id} card={card} />
          ) : (
            <WildfireAlertCard key={card.id} card={card} />
          )
        )}

        {/* Clear button */}
        {displayed.length > 0 && (
          <Button
            kind="ghost"
            size="sm"
            onClick={() => setLocalAlerts([])}
            style={{ width: '100%', color: 'var(--demo-text-muted)', marginTop: 4 }}
          >
            Clear alerts
          </Button>
        )}
      </div>
    </div>
  )
}
