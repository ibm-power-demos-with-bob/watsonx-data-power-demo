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
}: SourceCardProps) {
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

export default function DataSourcePanel() {
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
      </div>

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
          <SourceCard key={s.number} {...s} />
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
    </div>
  )
}
