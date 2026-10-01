/**
 * Page 1b — "The Federation Architecture" (/sources) — Why the Static Report Failed
 *
 * Sits between the Static Report (Page 1) and the Live View (Page 2).
 * Shows the audience exactly what data lives where and how watsonx.data
 * brings together Core ERP, Operational Data, and Live External Feeds
 * with the real-time AI detector running on IBM Power before triggering signals.
 * Each source's blindspot is explicitly linked to what the Static Report (Page 1) missed.
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { HeaderName } from '@carbon/react'
import { ArrowRight, Checkmark, Warning, ChevronDown, ChevronUp } from '@carbon/icons-react'
import { useAudience } from '../context/AudienceContext'

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
    // Explicit link to Page 1 (Static Map) omissions
    staticMapMissed: [
      'Supplier Status table: 50 tier-2 subcontractors invisible (Nexaflow compromised)',
      'KPI "Cyber Incidents: 0" — ERP never heard of the breach',
      'KPI "Active Suppliers: 53" — counts tier-1 only',
    ],
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
    staticMapMissed: [
      'Freight POs table: 3 POs on A9/AP-7 corridor — real-time route status unknown',
      'KPI "Freight Disruptions: 0" — route data frozen at Friday 06:00',
      'Supplier Status table: tier-2 graph exists here, not in ERP',
    ],
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
    staticMapMissed: [
      'KPI "Cyber Incidents: 0" — CISA KEV feed has the breach, ERP does not',
      'KPI "Freight Disruptions: 0" — route telemetry has the closure, ERP does not',
      'No live threat or route data anywhere in the Static Map',
    ],
    punchline: 'The live stream that reflects what is happening right now.',
  },
]

// Speaker notes for Architecture page
const ARCH_SPEAKER_NOTES = [
  {
    section: 'Opening — Why Three Sources? (30 sec)',
    points: [
      'Point to the three cards: "Your ERP (IBM i) knows your orders and tier-1 suppliers. Your operational DB (PostgreSQL/EDB) knows the tier-2 graph and warehouse routes. Your live stream (Iceberg) knows the threats and road conditions right now."',
      'The problem: "They never talk to each other. The Static Map on Page 1 only saw the ERP view — green everywhere."',
      'The solution: "watsonx.data federates them. No ETL. No data movement. A single query joins all three in <2 seconds."',
    ],
  },
  {
    section: 'Source 1 — IBM i ERP (45 sec)',
    points: [
      '"99k orders, 32k products — this is your system of record. On real IBM Power. Real Db2 for i."',
      'Tap the blindspot: "But it knows nothing of Nexaflow Logistics. That tier-2 supplier lives in Source 2."',
      'Connect to Page 1: "That\'s why the Static Map showed Cyber Incidents: 0. The breach was in Source 2 + 3, not here."',
    ],
  },
  {
    section: 'Source 2 — Operational Data / EDB Postgres (45 sec)',
    points: [
      '"50 subcontractors, 12 warehouses, freight corridor mappings. This is where the tier-2 graph lives — who supplies your suppliers."',
      'Tap the blindspot: "But it has no link to live orders. It knows Nexaflow is compromised, but not which POs are at risk."',
      'Connect to Page 1: "That\'s why the Freight POs table showed ON TRACK for A9/AP-7 routes. The corridor mapping is here; the live closure is in Source 3."',
    ],
  },
  {
    section: 'Source 3 — Real-Time Stream / Iceberg (45 sec)',
    points: [
      '"Live POS transactions, CISA Known Exploited Vulnerabilities feed, route telemetry. This is the outside world talking to you."',
      'Tap the blindspot: "But it has no corporate context. It knows a road closed; it doesn\'t know your POs use that road."',
      'Connect to Page 1: "That\'s why the Static Map knew nothing. The signals exist here — but without federation to Sources 1 & 2, they\'re just noise."',
    ],
  },
  {
    section: 'The Satnav Engine Reveal (30 sec)',
    points: [
      'Point to the banner below: "This is the satnav engine. When a signal arrives in Source 3, the detector instantly joins it to Source 2 (who\'s affected?) and Source 1 (what\'s the exposure?)."',
      '"In production: continuous pipeline (polling CISA KEV, route webhooks, Kafka/Flink) auto-triggers this same federation. In demo: we click a button to show you the moment."',
      'Click "Launch Live Satnav" → Navigate to /live?scenario=cyber',
    ],
  },
]

export default function SourcesPage() {
  const router = useRouter()
  const [showNotes, setShowNotes] = useState(false)
  const { isSecurity, isTechnical, isExecutive, isOperations } = useAudience()

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
          <HeaderName prefix="IBM" href="/" style={{ paddingLeft: 0, textDecoration: 'none' }}>
            watsonx.data on IBM Power
          </HeaderName>
          <span style={{ fontSize: 12, color: '#8d8d8d', borderLeft: '1px solid #393939', paddingLeft: 16 }}>
            Architecture &amp; Data Federation
          </span>
          <div style={{ flex: 1 }} />
          <button
            onClick={() => setShowNotes(!showNotes)}
            style={{
              background: showNotes ? '#0f62fe' : 'transparent',
              border: '1px solid #0f62fe',
              color: showNotes ? '#ffffff' : '#0f62fe',
              borderRadius: 2,
              padding: '4px 10px',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
            title="Toggle speaker notes for rehearsal"
          >
            {showNotes ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            <span>Speaker Notes</span>
          </button>
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
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, color: '#ffffff' }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: '#8d8d8d' }}>{s.tech}</div>
                  </div>
                  {/* Audience-specific relevance badge */}
                  {(s.num === '1' && isExecutive) && (
                    <span style={{ background: '#0f62fe22', border: '1px solid #0f62fe', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#0f62fe', textTransform: 'uppercase' }}>
                      ERP OWNER
                    </span>
                  )}
                  {(s.num === '2' && isOperations) && (
                    <span style={{ background: '#f1c21b22', border: '1px solid #f1c21b', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#f1c21b', textTransform: 'uppercase' }}>
                      TIER-2 GRAPH
                    </span>
                  )}
                  {(s.num === '3' && isSecurity) && (
                    <span style={{ background: '#da1e2822', border: '1px solid #da1e28', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#da1e28', textTransform: 'uppercase' }}>
                      THREAT FEED
                    </span>
                  )}
                  {(s.num === '3' && isTechnical) && (
                    <span style={{ background: '#08bdba22', border: '1px solid #08bdba', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#08bdba', textTransform: 'uppercase' }}>
                      ICEBERG STREAM
                    </span>
                  )}
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

                {/* What the Static Map Missed — Cross-reference to Page 1 */}
                <div
                  style={{
                    background: '#1a1a2e',
                    borderLeft: '3px solid #0f62fe',
                    padding: '8px 10px',
                    fontSize: 11,
                    color: '#b3d7ff',
                    marginBottom: 12,
                    lineHeight: 1.5,
                    border: '1px solid #1d4ed8',
                    borderRadius: '0 2px 2px 0',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <span style={{ fontSize: 12, color: '#0f62fe', flexShrink: 0, fontWeight: 700 }}>ℹ</span>
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#0f62fe', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      What the Static Map (Page 1) Missed
                    </span>
                  </div>
                  {s.staticMapMissed.map((m, i) => (
                    <div key={i} style={{ display: 'flex', gap: 6, fontSize: 11, color: '#c6c6c6', marginBottom: 3, lineHeight: 1.4 }}>
                      <span style={{ color: '#0f62fe', flexShrink: 0 }}>→</span>
                      <span>{m}</span>
                    </div>
                  ))}
                </div>

                {/* Punchline */}
                <div style={{ fontSize: 11, fontStyle: 'italic', color: '#8d8d8d', borderTop: '1px solid #393939', paddingTop: 8 }}>
                  {s.punchline}
                </div>
              </div>
            ))}
          </div>

          {/* Satnav Flow Diagram — How Detection Works */}
          <div
            style={{
              background: '#161616',
              border: '1px solid #393939',
              borderRadius: 4,
              padding: '20px 24px',
              marginBottom: 24,
            }}
          >
            <div style={{ fontSize: 12, color: '#4589ff', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 16 }}>
              The Satnav Engine — How Detection Works
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
              {/* Step 1: External Signal */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%',
                  background: '#06b6d422', border: '2px solid #06b6d4',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 24, color: '#06b6d4',
                }}>
                  📡
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#ffffff', textAlign: 'center' }}>External Signal</div>
                <div style={{ fontSize: 10, color: '#8d8d8d', textAlign: 'center', maxWidth: 120 }}>
                  CISA KEV Feed / Route Telemetry / Weather API
                </div>
              </div>
              <span style={{ color: '#525252', fontSize: 18 }}>→</span>
              {/* Step 2: Iceberg Ingestion */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%',
                  background: '#a855f722', border: '2px solid #a855f7',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 24, color: '#a855f7',
                }}>
                  ❄
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#ffffff', textAlign: 'center' }}>Iceberg Lakehouse</div>
                <div style={{ fontSize: 10, color: '#8d8d8d', textAlign: 'center', maxWidth: 120 }}>
                  Signal normalised, enriched, stored in watsonx.data
                </div>
              </div>
              <span style={{ color: '#525252', fontSize: 18 }}>→</span>
              {/* Step 3: Federation Query */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%',
                  background: '#4589ff22', border: '2px solid #4589ff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 24, color: '#4589ff',
                }}>
                  🔗
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#ffffff', textAlign: 'center' }}>Federated Query</div>
                <div style={{ fontSize: 10, color: '#8d8d8d', textAlign: 'center', maxWidth: 120 }}>
                  Presto joins IBM i × PostgreSQL × Iceberg in &lt;2s
                </div>
              </div>
              <span style={{ color: '#525252', fontSize: 18 }}>→</span>
              {/* Step 4: Alert & Action */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%',
                  background: '#24a14822', border: '2px solid #24a148',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 24, color: '#24a148',
                }}>
                  ⚡
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#ffffff', textAlign: 'center' }}>Alert + Action</div>
                <div style={{ fontSize: 10, color: '#8d8d8d', textAlign: 'center', maxWidth: 120 }}>
                  Quantified exposure → SIEM / PagerDuty / Auto-remediation
                </div>
              </div>
            </div>
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #393939', fontSize: 11, color: '#8d8d8d', textAlign: 'center' }}>
              <strong style={{ color: '#0f62fe' }}>Demo:</strong> Button click triggers this flow.
              <strong style={{ color: '#08bdba', marginLeft: 16 }}>Production:</strong> Continuous pipeline (CISA KEV polling 5-min, route webhooks, Kafka/Flink) auto-triggers same query → SIEM/SOAR.
            </div>
          </div>

          {/* The Satnav Engine Banner */}
          <div
            style={{
              background: 'linear-gradient(90deg, #0f172a 0%, #1e112a 50%, #081d24 100%)',
              border: '1px solid #08bdba',
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
                border: '2px solid #08bdba',
                color: '#08bdba',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                flexShrink: 0,
              }}
            >
              🧭
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14, color: '#ffffff', marginBottom: 4 }}>
                The Satnav Engine: Real-Time Detection on IBM Power
              </div>
              <div style={{ fontSize: 12, color: '#a8a8a8', lineHeight: 1.5 }}>
                When a signal arrives in the live stream (Source 3), the detector instantly federates across
                <strong style={{ color: '#4589ff' }}>Core ERP (IBM i)</strong> and
                <strong style={{ color: '#a855f7' }}>Operational Data (PostgreSQL/EDB)</strong> —
                joining the external event to your internal supplier dependencies and delivery lanes in <strong>&lt;2 seconds</strong>.
                Normal events pass through quietly; matches surface quantified exposure immediately.
              </div>
              <div style={{ fontSize: 11, color: '#08bdba', marginTop: 8, fontWeight: 600 }}>
                In production: continuous ingestion pipeline auto-triggers this federation. In demo: we inject the signal to show you the moment.
              </div>
            </div>
            <button
              onClick={() => router.push('/live?scenario=cyber')}
              style={{
                background: '#0f62fe',
                color: '#ffffff',
                border: 'none',
                borderRadius: 2,
                padding: '14px 28px',
                fontSize: 15,
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                whiteSpace: 'nowrap',
                boxShadow: '0 4px 12px rgba(15, 98, 254, 0.3)',
              }}
            >
              Launch Live Satnav — Scenario 1 (Cyber) <ArrowRight size={18} />
            </button>
          </div>

          {/* Speaker Notes Panel (Collapsible) */}
          {showNotes && (
            <div style={{
              background: '#161616',
              border: '1px solid #393939',
              borderRadius: 4,
              padding: '20px 24px',
              color: '#f4f4f4',
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
                paddingBottom: 12,
                borderBottom: '1px solid #393939',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 18, color: '#0f62fe', fontWeight: 700 }}>ℹ</span>
                  <span style={{ fontWeight: 700, fontSize: 14 }}>Speaker Notes — Rehearsal Mode</span>
                </div>
                <button
                  onClick={() => setShowNotes(false)}
                  style={{
                    background: 'transparent',
                    border: '1px solid #525252',
                    color: '#c6c6c6',
                    borderRadius: 2,
                    padding: '4px 10px',
                    fontSize: 11,
                    cursor: 'pointer',
                  }}
                >
                  Hide Notes
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                {ARCH_SPEAKER_NOTES.map((note, idx) => (
                  <div key={idx} style={{
                    background: '#1e1e1e',
                    border: '1px solid #393939',
                    borderRadius: 2,
                    padding: '14px 16px',
                  }}>
                    <div style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: '#0f62fe',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      marginBottom: 8,
                      borderBottom: '1px solid #393939',
                      paddingBottom: 6,
                    }}>
                      {note.section}
                    </div>
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#c6c6c6', lineHeight: 1.7 }}>
                      {note.points.map((p, pi) => (
                        <li key={pi}>{p}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
              <div style={{
                marginTop: 16,
                paddingTop: 12,
                borderTop: '1px solid #393939',
                fontSize: 11,
                color: '#8d8d8d',
                fontStyle: 'italic',
              }}>
                💡 Tip: Print this panel or keep it open on a second screen during the demo. Click "Speaker Notes" in the header to toggle.
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  )
}
