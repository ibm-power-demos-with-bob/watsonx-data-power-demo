/**
 * DataSourcePanel
 *
 * Architecture talking point panel — the "three sources" diagram.
 * Labelled IBM i / EDB Postgres / Apache Iceberg with the key narrative
 * for each source.  This is the slide the presenter keeps on screen during
 * the data-source walk-through section of the demo arc.
 *
 * Renders status indicators that can be set to 'connected' | 'stub' | 'offline'
 * so the presenter can see at a glance which sources are live vs. simulated.
 */

'use client'
import { useState } from 'react'

interface SourceCardProps {
  number: string
  title: string
  subtitle: string
  technology: string
  colour: string
  badgeClass: string
  tables: string[]
  narrative: string
  status: 'connected' | 'stub' | 'offline'
  isSecurity?: boolean
  isTechnical?: boolean
  isExecutive?: boolean
  isOperations?: boolean
}

function StatusDot({ status }: { status: SourceCardProps['status'] }) {
  const cfg = {
    connected: { color: 'var(--demo-green)',  label: 'CONNECTED' },
    stub:      { color: 'var(--demo-yellow)', label: 'SIMULATED' },
    offline:   { color: 'var(--demo-text-muted)', label: 'OFFLINE' },
  }[status]
  return (
    <span
      style={{
        fontSize: 10,
        color: cfg.color,
        fontWeight: 600,
        letterSpacing: '0.05em',
        display: 'flex',
        alignItems: 'center',
        gap: 4,
      }}
    >
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: cfg.color,
          flexShrink: 0,
          display: 'inline-block',
        }}
      />
      {cfg.label}
    </span>
  )
}

function SourceCard({
  number,
  title,
  subtitle,
  technology,
  colour,
  badgeClass,
  tables,
  narrative,
  status,
  isSecurity,
  isTechnical,
  isExecutive,
  isOperations,
}: SourceCardProps) {
  
  // Audience-specific relevance badge
  const audienceBadge = (number === '1' && isExecutive) ? (
    <span style={{ background: '#0f62fe22', border: '1px solid #0f62fe', borderRadius: 2, padding: '2px 6px', fontSize: 8, fontWeight: 600, color: '#0f62fe', textTransform: 'uppercase' }}>ERP OWNER</span>
  ) : (number === '2' && isOperations) ? (
    <span style={{ background: '#f1c21b22', border: '1px solid #f1c21b', borderRadius: 2, padding: '2px 6px', fontSize: 8, fontWeight: 600, color: '#f1c21b', textTransform: 'uppercase' }}>TIER-2 GRAPH</span>
  ) : (number === '3' && isSecurity) ? (
    <span style={{ background: '#da1e2822', border: '1px solid #da1e28', borderRadius: 2, padding: '2px 6px', fontSize: 8, fontWeight: 600, color: '#da1e28', textTransform: 'uppercase' }}>THREAT FEED</span>
  ) : (number === '3' && isTechnical) ? (
    <span style={{ background: '#08bdba22', border: '1px solid #08bdba', borderRadius: 2, padding: '2px 6px', fontSize: 8, fontWeight: 600, color: '#08bdba', textTransform: 'uppercase' }}>ICEBERG</span>
  ) : null

  return (
    <div
      style={{
        background: 'var(--demo-surface)',
        border: `1px solid ${colour}55`,
        borderLeft: `3px solid ${colour}`,
        borderRadius: 2,
        padding: '14px',
        flex: 1,
        minWidth: 0,
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <div
          style={{
            background: colour + '22',
            border: `1px solid ${colour}44`,
            borderRadius: '50%',
            width: 26,
            height: 26,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            fontSize: 12,
            fontWeight: 700,
            color: colour,
          }}
        >
          {number}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--demo-text)', marginBottom: 1 }}>
            {title}
          </div>
          <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>{subtitle}</div>
        </div>
        {audienceBadge}
        <StatusDot status={status} />
      </div>

      {/* Technology badge */}
      <div style={{ marginBottom: 10 }}>
        <span className={`source-badge ${badgeClass}`}>{technology}</span>
      </div>

      {/* Tables */}
      <div style={{ marginBottom: 10 }}>
        <div
          style={{
            fontSize: 10,
            color: 'var(--demo-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: 4,
          }}
        >
          Tables / Streams
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {tables.map((t) => (
            <span
              key={t}
              style={{
                fontFamily: 'IBM Plex Mono, monospace',
                fontSize: 10,
                background: 'var(--demo-surface-2)',
                border: '1px solid var(--demo-border)',
                borderRadius: 2,
                padding: '2px 6px',
                color: 'var(--demo-text-muted)',
              }}
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Narrative */}
      <div
        style={{
          fontSize: 11,
          color: 'var(--demo-text-muted)',
          lineHeight: 1.6,
          borderTop: '1px solid var(--demo-border)',
          paddingTop: 8,
          fontStyle: 'italic',
        }}
      >
        {narrative}
      </div>
    </div>
  )
}

const SOURCES: SourceCardProps[] = [
  {
    number: '1',
    title: 'IBM i — Core ERP',
    subtitle: 'Db2 for IBM i · Power10 LPAR · TechZone Poughkeepsie',
    technology: '⚙ Db2 for IBM i',
    colour: '#4589ff',
    badgeClass: 'badge-ibmi',
    tables: ['OLIST.CUSTOMERS', 'OLIST.PRODUCTS', 'OLIST.ORDERS', 'OLIST.ORDERITEMS'],
    narrative:
      'The authentic Power element. 99k+ orders, 32k products with SECTOR classification. ' +
      'Tier-1 suppliers are visible here — but tier-2 sub-contractors are not. ' +
      'Running IBM i alongside a modern lakehouse is news to most audiences.',
    status: 'connected',
  },
  {
    number: '2',
    title: 'EDB Postgres — Operational DB',
    subtitle: 'EDB Postgres · RHEL/Power10 VM · TechZone',
    technology: '🐘 EDB Postgres',
    colour: '#be95ff',
    badgeClass: 'badge-edb',
    tables: ['olist.suppliers', 'olist.tier2_suppliers', 'olist.warehouses', 'olist.purchase_orders'],
    narrative:
      'Stands in for the Oracle-on-AIX estate. Holds the tier-2 logistics sub-contractors ' +
      '(Nexaflow, Alderton, Castleton, Greystone) — the gap your ERP cannot see. ' +
      'The federation punchline lives here.',
    status: 'stub',
  },
  {
    number: '3',
    title: 'Apache Iceberg — Event & Signal Stream',
    subtitle: 'Iceberg on COS · watsonx.data SaaS · IBM Cloud London',
    technology: '⬡ Apache Iceberg',
    colour: '#08bdba',
    badgeClass: 'badge-iceberg',
    tables: ['retail.retail_pos_events', 'retail.retail_signals'],
    narrative:
      'The live event streaming tier. Ingests POS transactions alongside external intelligence signals: ' +
      'Cybersecurity Threat Intelligence (live Known Exploited Vulnerabilities early warning) and Route & Travel Disruption Intelligence (freight corridors). ' +
      'The watsonx.data detector joins incoming signals against IBM i ERP & EDB context in under 2 seconds.',
    status: 'stub',
  },
]

// Live federation SQL queries for both scenarios
const LIVE_QUERIES = {
  'supplier-cyber-incident': {
    title: 'Cyber Incident — Federated Exposure Query',
    description: 'Joins CISA KEV signal (Iceberg) → tier-2 supplier graph (EDB) → open POs & customer exposure (IBM i)',
    sql: `-- Federated Cyber Exposure Query
-- Runs in <2 seconds on Presto (watsonx.data) across 3 sources

SELECT
  COUNT(po.po_number)                         AS open_po_count,
  COUNT(DISTINCT s.supplier_id)               AS tier1_suppliers_affected,
  CAST(SUM(po.unit_price + po.freight_value) AS DOUBLE) AS total_exposure_gbp,
  MIN(CAST(po.ship_limit_date AS VARCHAR(30))) AS earliest_order,
  SUM(CASE WHEN po.po_status = 'OPEN' THEN 1 ELSE 0 END) AS critical_pos_7_days
FROM pg_olist.olist.v_purchase_orders po
JOIN pg_olist.olist.v_suppliers s
  ON po.supplier_id = s.supplier_id
JOIN pg_olist.olist.v_tier2_suppliers t2
  ON s.subcontracted_to_id = t2.tier2_id
JOIN ibmi_olist.OLIST.ORDERS o
  ON po.customer_id = o."customer id"
WHERE t2.company_name = 'Nexaflow Logistics Ltd'
  AND t2.breach_status = 'COMPROMISED'
  AND o."order date" >= CURRENT_DATE - 30 DAYS;`,
  },
  'eu-wildfire': {
    title: 'Wildfire Corridor — At-Risk POs Query',
    description: 'Joins route disruption signal (Iceberg) → warehouse corridors (EDB) → active freight POs (IBM i)',
    sql: `-- Federated Wildfire Exposure Query
-- Runs in <2 seconds on Presto (watsonx.data) across 3 sources

SELECT
  po.po_number,
  CAST(po.unit_price + po.freight_value AS DOUBLE) AS order_value,
  w.region_label                                   AS supplier_region,
  o."customer id"                                  AS customer_id,
  o."order id"                                     AS order_id
FROM pg_olist.olist.v_purchase_orders po
JOIN pg_olist.olist.v_warehouses w
  ON po.warehouse_id = w.warehouse_id
JOIN ibmi_olist.OLIST.ORDERS o
  ON po.customer_id = o."customer id"
WHERE w.region_label IN ('South France', 'Catalonia', 'Mediterranean')
  AND po.po_status = 'OPEN'
  AND o."order date" >= CURRENT_DATE - 30 DAYS
ORDER BY po.ship_limit_date ASC
LIMIT 10;`,
  },
}

export default function DataSourcePanel({ scenario, queryExecuting, isSecurity, isTechnical, isExecutive, isOperations }: { scenario?: 'supplier-cyber-incident' | 'eu-wildfire'; queryExecuting?: boolean; isSecurity?: boolean; isTechnical?: boolean; isExecutive?: boolean; isOperations?: boolean }) {
  const [activeTab, setActiveTab] = useState<'architecture' | 'live-query'>('architecture')
  const query = scenario ? LIVE_QUERIES[scenario] : null

  // Audience-specific tab visibility: hide Live Query tab for non-technical audiences
  const showLiveQueryTab = isTechnical || isSecurity || query !== null

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
        <span style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.02em', flex: 1 }}>
          DATA SOURCES
        </span>
        <span style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>
          watsonx.data Federation
        </span>
        {(isSecurity || isTechnical || isExecutive || isOperations) && (
          <span style={{
            background: 'var(--demo-surface-2)',
            border: '1px solid var(--demo-border)',
            borderRadius: 12,
            padding: '2px 8px',
            fontSize: 9,
            fontWeight: 600,
            color: isSecurity ? 'var(--demo-red)' : isTechnical ? 'var(--demo-purple)' : isOperations ? 'var(--demo-green)' : 'var(--demo-blue)',
            textTransform: 'uppercase',
          }}>
            {isSecurity && '🔒 SEC'}
            {isTechnical && '🔧 TECH'}
            {isOperations && '📦 OPS'}
            {isExecutive && '🎯 EXEC'}
          </span>
        )}
      </div>

      {/* Tab Navigation */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--demo-border)',
          background: 'var(--demo-surface)',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setActiveTab('architecture')}
          style={{
            padding: '8px 16px',
            border: 'none',
            background: activeTab === 'architecture' ? 'var(--demo-bg)' : 'transparent',
            color: activeTab === 'architecture' ? 'var(--demo-text)' : 'var(--demo-text-muted)',
            fontSize: 11,
            fontWeight: activeTab === 'architecture' ? 600 : 400,
            borderBottom: activeTab === 'architecture' ? '2px solid var(--demo-blue)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          🏗 Architecture
        </button>
        {query && showLiveQueryTab && (
          <button
            onClick={() => setActiveTab('live-query')}
            style={{
              padding: '8px 16px',
              border: 'none',
              background: activeTab === 'live-query' ? 'var(--demo-bg)' : 'transparent',
              color: activeTab === 'live-query' ? 'var(--demo-blue)' : 'var(--demo-text-muted)',
              fontSize: 11,
              fontWeight: activeTab === 'live-query' ? 600 : 400,
              borderBottom: activeTab === 'live-query' ? '2px solid var(--demo-blue)' : '2px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            🔍 Live Query
            {queryExecuting && (
              <span style={{
                width: 10, height: 10, borderRadius: '50%',
                border: '2px solid var(--demo-blue)', borderTopColor: 'transparent',
                animation: 'spin 1s linear infinite',
              }} />
            )}
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'architecture' && (
          <>
            {/* The satnav strapline */}
            <div
              style={{
                padding: '8px 16px',
                borderBottom: '1px solid var(--demo-border)',
                background: 'var(--demo-surface)',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--demo-text-muted)',
                  lineHeight: 1.5,
                  borderLeft: '3px solid var(--demo-teal)',
                  paddingLeft: 10,
                }}
              >
                <strong style={{ color: 'var(--demo-text)' }}>Map vs. satnav.</strong> A static report
                shows what was true last night. This demo shows three live sources joined in real time —
                the gap your ERP cannot see, found in seconds.
              </div>
            </div>

            {/* Source cards */}
            <div
              style={{
                flex: 1,
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                overflowY: 'auto',
              }}
            >
              {SOURCES.map((s) => (
                  <SourceCard
                    key={s.number}
                    {...s}
                    isSecurity={isSecurity}
                    isTechnical={isTechnical}
                    isExecutive={isExecutive}
                    isOperations={isOperations}
                  />
                ))}
            </div>

            {/* Power hardware footnote */}
            <div
              style={{
                padding: '8px 16px',
                borderTop: '1px solid var(--demo-border)',
                fontSize: 11,
                color: 'var(--demo-text-muted)',
                lineHeight: 1.5,
                background: 'var(--demo-surface)',
                flexShrink: 0,
              }}
            >
              <strong style={{ color: '#78a9ff' }}>IBM Power</strong> · Source 1 runs on a real
              IBM Power LPAR. This dashboard and continuous detector run on a RHEL/IBM Power VM — genuine Power
              hardware, with built-in MMA acceleration ready for optional on-box AI scoring.
            </div>
          </>
        )}

        {activeTab === 'live-query' && query && (
          <div style={{ padding: '16px', overflowY: 'auto', flex: 1 }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--demo-text)', marginBottom: 4 }}>
                {query.title}
              </div>
              <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginBottom: 12 }}>
                {query.description}
              </div>
              {queryExecuting && (
                <div style={{
                  padding: '8px 12px',
                  background: '#1a1a2e',
                  border: '1px solid var(--demo-blue)',
                  borderRadius: 2,
                  marginBottom: 12,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 11,
                  color: 'var(--demo-blue)',
                  fontWeight: 600,
                  fontFamily: 'IBM Plex Mono, monospace',
                }}>
                  <span style={{
                    width: 14, height: 14, borderRadius: '50%',
                    border: '2px solid var(--demo-blue)', borderTopColor: 'transparent',
                    animation: 'spin 1s linear infinite',
                    }} />
                    Executing federated query across 3 sources... {'<2s'}
                  </div>
              )}
            </div>
            <div style={{
              background: '#0d0d0d',
              border: '1px solid var(--demo-border)',
              borderRadius: 2,
              padding: '16px',
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: 10,
              lineHeight: 1.6,
              color: '#b8e6b8',
              overflowX: 'auto',
              whiteSpace: 'pre',
            }}>
              {query.sql}
            </div>
            <div style={{ marginTop: 12, fontSize: 11, color: 'var(--demo-text-muted)', lineHeight: 1.5 }}>
              <strong>Sources joined:</strong>
              <span style={{ marginLeft: 8, color: '#4589ff' }}>IBM i (ibmi_olist)</span>
              <span style={{ marginLeft: 8, color: '#be95ff' }}>EDB Postgres (pg_olist)</span>
              <span style={{ marginLeft: 8, color: '#08bdba' }}>Iceberg (retail_signals)</span>
              <br />
              <strong>Execution:</strong> Presto (watsonx.data) federated query, zero-ETL, {'<2s typical'}.
              <br />
              <strong>Production note:</strong> Same SQL auto-executed by stream processor on signal match.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
