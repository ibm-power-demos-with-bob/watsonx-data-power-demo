/**
 * Page 1b — "The Federation Architecture" (/sources)
 *
 * Sits between the Static Report (Page 1) and the Live Satnav (Page 2).
 * Shows the audience exactly what data lives where and how watsonx.data
 * brings together Core ERP, Operational Data, and Live External Feeds
 * with the real-time AI detector running on IBM Power before triggering signals.
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { ArrowRight, Checkmark, Warning } from '@carbon/icons-react'

const SOURCES = [
  {
    num: '1',
    name: 'Core ERP — IBM i',
    tech: 'Db2 for IBM i · IBM Power LPAR',
    badge: 'badge-ibmi',
    color: '#4589ff',
    bg: '#0f172a',
    borderColor: '#1d4ed8',
    records: '99,441 Orders · 32,951 Products',
    heldData: [
      'Customer master & order header records',
      'Product catalog with SECTOR tags',
      'Tier-1 Direct Suppliers (invoicing entities)',
    ],
    blindspot: 'Cannot see tier-2 subcontractors or live road/threat feeds.',
    punchline: 'The authoritative system of record — on authentic IBM Power.',
  },
  {
    num: '2',
    name: 'Operational Data — EDB Postgres',
    tech: 'PostgreSQL · RHEL on IBM Power',
    badge: 'badge-edb',
    color: '#a855f7',
    bg: '#1e112a',
    borderColor: '#7e22ce',
    records: '50 Subcontractors · 12 Warehouses · Route Graph',
    heldData: [
      'Tier-2 logistics subcontractors (Nexaflow, etc.)',
      'Regional distribution center coordinates',
      'Freight corridor mappings (A9/AP-7, Alpine routes)',
    ],
    blindspot: 'Has no direct link to live sales orders or current customer exposure.',
    punchline: 'Stands in for enterprise operations (Oracle/Postgres estates).',
  },
  {
    num: '3',
    name: 'Real-Time Stream — Apache Iceberg',
    tech: 'Apache Iceberg on Cloud Object Storage · watsonx.data',
    badge: 'badge-iceberg',
    color: '#06b6d4',
    bg: '#081d24',
    borderColor: '#0e7490',
    records: 'Live POS Transactions + Upstream Intelligence Feeds',
    heldData: [
      'Live POS transactions across 21 stores',
      'Cyber Threat Intelligence (Known Exploited Vulnerabilities)',
      'Freight corridor sensor & road disruption telemetry',
    ],
    blindspot: 'Unstructured/streaming signals without corporate ERP context.',
    punchline: 'The live stream that reflects what is happening right now.',
  },
]

export default function SourcesPage() {
  const router = useRouter()

  return (
    <>
      <Head>
        <title>Federation Architecture — watsonx.data on IBM Power</title>
      </Head>

      <div
        style={{
          minHeight: '100vh',
          background: '#121619',
          fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
          color: '#f4f4f4',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header bar */}
        <header
          style={{
            height: 56,
            background: '#161616',
            borderBottom: '1px solid #393939',
            padding: '0 32px',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            flexShrink: 0,
          }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 24" width="42" height="17" aria-label="IBM">
            <path
              fill="#0f62fe"
              d="M0 18.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm13 13.5h26v-2H13v2zm4-4.5h18v-2H17v2zm0-4.5h18v-2H17v2zm-4-4.5h26v-2H13v2zm30 13.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2z"
            />
          </svg>
          <span style={{ fontWeight: 700, fontSize: 14, color: '#f4f4f4' }}>watsonx.data on IBM Power</span>
          <span style={{ fontSize: 12, color: '#8d8d8d', borderLeft: '1px solid #393939', paddingLeft: 16 }}>
            Architecture &amp; Data Federation
          </span>
          <div style={{ flex: 1 }} />
          <button
            onClick={() => router.push('/')}
            style={{
              background: 'transparent',
              border: '1px solid #525252',
              color: '#c6c6c6',
              borderRadius: 2,
              padding: '6px 14px',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            ← Back to Static Report
          </button>
        </header>

        {/* Main Content */}
        <div style={{ padding: '32px', maxWidth: 1280, margin: '0 auto', flex: 1, width: '100%' }}>
          {/* Section title */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 12, color: '#4589ff', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 6 }}>
              The Power of Zero-ETL Federation
            </div>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: '#ffffff', margin: 0, marginBottom: 8 }}>
              Three Disparate Sources. Joined in Seconds by watsonx.data.
            </h1>
            <p style={{ fontSize: 14, color: '#a8a8a8', maxWidth: 850, lineHeight: 1.6, margin: 0 }}>
              Traditional BI relies on static overnight reports because ERP, operational, and external feeds live in separate silos.
              watsonx.data federates these systems directly where they sit — without moving or transforming data.
            </p>
          </div>

          {/* Three Sources Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 28 }}>
            {SOURCES.map((s) => (
              <div
                key={s.num}
                style={{
                  background: s.bg,
                  border: `1px solid ${s.borderColor}`,
                  borderTop: `4px solid ${s.color}`,
                  borderRadius: 4,
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: `${s.color}22`,
                      color: s.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: 13,
                    }}
                  >
                    {s.num}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15, color: '#ffffff' }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: '#8d8d8d' }}>{s.tech}</div>
                  </div>
                </div>

                {/* Records volume */}
                <div
                  style={{
                    background: '#161616',
                    border: '1px solid #393939',
                    borderRadius: 2,
                    padding: '6px 10px',
                    fontSize: 11,
                    fontFamily: 'IBM Plex Mono, monospace',
                    color: s.color,
                    marginBottom: 14,
                  }}
                >
                  📊 {s.records}
                </div>

                {/* What it holds */}
                <div style={{ flex: 1, marginBottom: 14 }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', color: '#8d8d8d', fontWeight: 600, marginBottom: 6 }}>
                    What this source holds:
                  </div>
                  {s.heldData.map((d, i) => (
                    <div key={i} style={{ display: 'flex', gap: 6, fontSize: 12, color: '#c6c6c6', marginBottom: 4, lineHeight: 1.4 }}>
                      <Checkmark size={14} style={{ color: s.color, flexShrink: 0, marginTop: 2 }} />
                      <span>{d}</span>
                    </div>
                  ))}
                </div>

                {/* Blindspot */}
                <div
                  style={{
                    background: '#261a1a',
                    borderLeft: '3px solid #da1e28',
                    padding: '8px 10px',
                    fontSize: 11,
                    color: '#ffb3b8',
                    marginBottom: 12,
                    lineHeight: 1.4,
                  }}
                >
                  <strong style={{ color: '#fa4d56' }}>Blindspot:</strong> {s.blindspot}
                </div>

                {/* Punchline */}
                <div style={{ fontSize: 11, fontStyle: 'italic', color: '#8d8d8d', borderTop: '1px solid #393939', paddingTop: 8 }}>
                  {s.punchline}
                </div>
              </div>
            ))}
          </div>

          {/* Real-time Join & MMA Detector Banner */}
          <div
            style={{
              background: '#161616',
              border: '1px solid #393939',
              borderRadius: 4,
              padding: '20px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              marginBottom: 32,
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                background: '#08bdba22',
                border: '1px solid #08bdba44',
                color: '#08bdba',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                flexShrink: 0,
              }}
            >
              ⚡
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14, color: '#ffffff', marginBottom: 4 }}>
                Real-Time Continuous Detection &amp; Federation on IBM Power
              </div>
              <div style={{ fontSize: 12, color: '#a8a8a8', lineHeight: 1.5 }}>
                The real-time detector running on IBM Power continuously monitors live external threat streams and route telemetry, cross-referencing them against corporate data. Normal events pass through quietly; when an incident matches internal supplier dependencies or delivery lanes, federated queries join the disparate sources in &lt;2 seconds — enabling immediate, proactive human or automated response. Optional AI scoring (MMA-accelerated on Power) can further prioritize risks as transaction volume scales.
              </div>
            </div>
            <button
              onClick={() => router.push('/live?scenario=cyber')}
              style={{
                background: '#0f62fe',
                color: '#ffffff',
                border: 'none',
                borderRadius: 2,
                padding: '12px 24px',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                whiteSpace: 'nowrap',
              }}
            >
              Launch Live Satnav (Scenario 1) <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
