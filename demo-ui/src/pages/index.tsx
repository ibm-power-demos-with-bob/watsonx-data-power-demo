/**
 * Page 1 — "The Static Report"
 *
 * A mock weekly management report, last generated Friday 06:00.
 * Everything looks fine. Suppliers green. Freight on track.
 * This is the "before" state — the world as the business believes it is.
 * Confident, green, and wrong.
 *
 * Presenter script:
 * "This is what your business looks like based on your last report.
 *  Generated Friday morning at 6am. It's now Monday. Nothing unusual —
 *  all suppliers active, all freight on track, no flags.
 *  [pause]
 *  Let me show you what the report missed."
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { HeaderName } from '@carbon/react'
import { ChevronDown, ChevronUp, Warning } from '@carbon/icons-react'
import { useAudience } from '../context/AudienceContext'

const REPORT_DATE = 'Friday 22 Aug 2026 — 06:00 BST'
const VIEWED_DATE = 'Monday 25 Aug 2026 — 09:14 BST'

const SUPPLIER_DATA = [
  { id: 'SUP-001', name: 'Hartwell Distribution Ltd',    region: 'South East England', status: 'ACTIVE', orders: 14, value: '£47,230' },
  { id: 'SUP-002', name: 'Meridian Freight Services',    region: 'Midlands',           status: 'ACTIVE', orders: 9,  value: '£28,450' },
  { id: 'SUP-003', name: 'Castlegate Logistics',         region: 'North West',         status: 'ACTIVE', orders: 11, value: '£33,180' },
  { id: 'SUP-004', name: 'Alderton Supply Co.',          region: 'South West',         status: 'ACTIVE', orders: 7,  value: '£19,660' },
  { id: 'SUP-005', name: 'Greystone Courier Network',   region: 'Yorkshire',          status: 'ACTIVE', orders: 12, value: '£41,200' },
]

const FREIGHT_DATA = [
  { po: 'PO-2017-00142', route: 'Lyon → Barcelona (A9/AP-7)', eta: '27 Aug',  value: '£840',   status: 'ON TRACK' },
  { po: 'PO-2017-00198', route: 'Lyon → Barcelona (A9/AP-7)', eta: '29 Aug',  value: '£1,260', status: 'ON TRACK' },
  { po: 'PO-2017-00307', route: 'Lyon → Valencia (A9/AP-7)',  eta: '30 Aug',  value: '£510',   status: 'ON TRACK' },
  { po: 'PO-2017-00412', route: 'Paris → Madrid (A9)',        eta: '28 Aug',  value: '£2,100', status: 'ON TRACK' },
  { po: 'PO-2017-00501', route: 'Marseille → Barcelona',      eta: '26 Aug',  value: '£730',   status: 'ON TRACK' },
]

const KPI_DATA = [
  { label: 'Active Suppliers',     value: '53',    sub: 'vs 53 last week',  ok: true  },
  { label: 'Open Purchase Orders', value: '127',   sub: 'vs 119 last week', ok: true  },
  { label: 'On-Time Delivery',     value: '94.2%', sub: 'vs 93.8% last week', ok: true },
  { label: 'Cyber Incidents',      value: '0',     sub: 'No flags raised',  ok: true  },
  { label: 'Freight Disruptions',  value: '0',     sub: 'All routes clear',  ok: true  },
  { label: 'Stock Alerts',         value: '2',     sub: 'Low priority',     ok: true  },
]

// Speaker notes for presenter rehearsal — collapsible panel
const SPEAKER_NOTES = [
  {
    section: 'Opening (30 sec)',
    points: [
      'Hold up the weekly report (or point to the screen): "This is your last management report."',
      'Point to the date: "Generated Friday 6am. Today is Monday 9am."',
      'Tap the green badge: "All systems nominal. 53 suppliers active. Zero cyber incidents. Zero freight disruptions."',
      'Pause. "Comforting, isn\'t it? Now watch what happens when we inject reality."',
    ],
  },
  {
    section: 'KPIs — False Confidence (30 sec)',
    points: [
      'Cyber Incidents: 0 — "Your ERP has never heard of Nexaflow Logistics. They\'re a tier-2 subcontractor. The breach won\'t show up here until a tier-1 supplier calls to say they can\'t deliver."',
      'Freight Disruptions: 0 — "Route status is from Friday. The A9/AP-7 corridor could be closed right now and this report would still say \'All routes clear\'."',
      'Active Suppliers: 53 — "Tier-1 only. The 50 tier-2 subcontractors who actually move your goods? Invisible."',
    ],
  },
  {
    section: 'Supplier Table — The Blindspot (30 sec)',
    points: [
      'Point to the footnote: "Tier-2 sub-contractors are not visible in ERP."',
      'Name the risk: "Nexaflow Logistics Ltd — compromised via MOVEit (CVE-2023-34362). 14 open POs. £47k exposure. 6 tier-1 suppliers affected. None of this appears in this table."',
      'Transition: "The static report doesn\'t show the road closure. The live view does. Let me show you."',
    ],
  },
  {
    section: 'Freight Table — The Blindspot (30 sec)',
    points: [
      'Point to the footnote: "Route status based on Friday morning road network data. No real-time updates."',
      'Name the risk: "Three POs on the A9/AP-7 corridor. If a wildfire closes it today, you won\'t know until Monday\'s report — by which time ship limits are missed."',
    ],
  },
  {
    section: 'Closing & Transition (15 sec)',
    points: [
      '"This report isn\'t wrong — it\'s just 3 days old. In a static world, that\'s fine. In a world of zero-day exploits and climate-driven logistics disruption, it\'s dangerous."',
      'Click "See the Live Satnav" → Navigate to /sources',
    ],
  },
]

export default function StaticMapPage() {
  const router = useRouter()
  const [showNotes, setShowNotes] = useState(false)
  const { isSecurity, isTechnical, isExecutive, isOperations } = useAudience()

  return (
    <>
      <Head>
        <title>Weekly Operations Report — watsonx.data Demo</title>
      </Head>

      <div style={{
        minHeight: '100vh',
        background: '#f4f4f4',
        fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
        color: '#161616',
      }}>

        {/* ── Report header bar ── */}
        <div style={{
          background: '#ffffff',
          borderBottom: '1px solid #e0e0e0',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          height: 56,
          gap: 16,
        }}>
          <HeaderName prefix="IBM" href="/" style={{ paddingLeft: 0, color: '#161616', textDecoration: 'none' }}>
            <span style={{ fontWeight: 400, color: '#525252' }}>Supply Chain Risk Dashboard</span>
          </HeaderName>

          {/* Weekly Report label */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '4px 10px',
            background: '#f0f0f0',
            border: '1px solid #d0d0d0',
            borderRadius: 2,
            marginLeft: 8,
          }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: '#525252', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Weekly Report</span>
            <span style={{ fontSize: 10, color: '#8d8d8d', background: '#e0e0e0', padding: '1px 6px', borderRadius: 10 }}>3 Days Old</span>
          </div>
          
          <span style={{ fontWeight: 700, fontSize: 14, color: '#161616' }}>Supply Chain Operations</span>
          <span style={{ fontSize: 12, color: '#525252', borderLeft: '1px solid #e0e0e0', paddingLeft: 16 }}>
            Weekly Management Report
          </span>
          <div style={{ flex: 1 }} />
          {/* Stale timestamp — the whole point, now prominent */}
          <div style={{ textAlign: 'right', marginRight: 16 }}>
            <div style={{ fontSize: 10, color: '#da1e28', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>⚠ Report is 3 Days Stale</div>
            <div style={{ fontSize: 11, color: '#6f6f6f' }}>Generated</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#525252' }}>{REPORT_DATE}</div>
            <div style={{ fontSize: 10, color: '#da1e28', fontWeight: 600, marginTop: 2 }}>Viewing at {VIEWED_DATE}</div>
          </div>
          <div style={{
            background: '#defbe6',
            border: '1px solid #24a148',
            borderRadius: 12,
            padding: '3px 10px',
            fontSize: 11,
            fontWeight: 600,
            color: '#0e6027',
          }}>
            ● ALL SYSTEMS NOMINAL
          </div>
          {/* Speaker Notes Toggle */}
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
        </div>

        <div style={{ padding: '24px 32px', maxWidth: 1280, margin: '0 auto' }}>

          {/* ── Prominent Staleness Warning — The "Atlas is 3 Days Old" Moment ── */}
          <div style={{
            background: '#fff1f1',
            border: '2px solid #da1e28',
            borderRadius: 4,
            padding: '16px 20px',
            marginBottom: 24,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            flexWrap: 'wrap',
          }}>
            <div style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: '#da1e28',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              fontWeight: 700,
              flexShrink: 0,
            }}>
              3
            </div>
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#da1e28', marginBottom: 4 }}>
                This Report Is 3 Days Old
              </div>
              <div style={{ fontSize: 13, color: '#525252', lineHeight: 1.5 }}>
                Generated <strong>{REPORT_DATE}</strong> · You are viewing it <strong>{VIEWED_DATE}</strong>
              </div>
              <div style={{ fontSize: 12, color: '#da1e28', fontWeight: 600, marginTop: 4 }}>
                In 72 hours: a tier-2 supplier was compromised (MOVEit CVE-2023-34362) · a freight corridor closed (A9/AP-7 wildfire) · 14 POs at risk · £47k exposure · none of it is in this report
              </div>
            </div>
            <div style={{
              background: '#da1e28',
              color: '#ffffff',
              padding: '8px 16px',
              borderRadius: 2,
              fontSize: 12,
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}>
              This report shows where you were. Live federation shows where you're heading.
            </div>
          </div>

          {/* ── KPI row ── */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(6, 1fr)',
            gap: 12,
            marginBottom: 24,
          }}>
            {KPI_DATA.map((k) => (
              <div key={k.label} style={{
                background: '#ffffff',
                border: '1px solid #e0e0e0',
                borderTop: '3px solid #24a148',
                borderRadius: 2,
                padding: '16px',
                position: 'relative',
              }}>
                {/* "What this KPI cannot see" badge */}
                <div style={{
                  position: 'absolute',
                  top: -10,
                  right: 12,
                  background: '#fff1f1',
                  border: '1px solid #da1e28',
                  borderRadius: 10,
                  padding: '2px 8px',
                  fontSize: 9,
                  fontWeight: 600,
                  color: '#da1e28',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  Blindspot
                </div>
                <div style={{ fontSize: 11, color: '#6f6f6f', marginBottom: 4 }}>{k.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#161616', lineHeight: 1 }}>{k.value}</div>
                <div style={{ fontSize: 11, color: '#24a148', marginTop: 4 }}>↑ {k.sub}</div>
              </div>
            ))}
          </div>

          {/* ── KPI Blindspot Legend ── */}
          <div style={{
            background: '#fff8e1',
            border: '1px solid #f1c21b',
            borderRadius: 2,
            padding: '12px 16px',
            marginBottom: 24,
            fontSize: 11,
            color: '#525252',
            display: 'flex',
            flexWrap: 'wrap',
            gap: 16,
            alignItems: 'center',
          }}>
            <span style={{ fontWeight: 600, color: '#da1e28' }}>What these green KPIs cannot see:</span>
            {isSecurity && <span style={{ borderLeft: '2px solid #da1e28', paddingLeft: 8, fontWeight: 700, color: '#da1e28' }}>🔒 SECURITY FOCUS</span>}
            {isOperations && <span style={{ borderLeft: '2px solid #f1c21b', paddingLeft: 8, fontWeight: 700, color: '#f1c21b' }}>📦 OPS FOCUS</span>}
            {isExecutive && <span style={{ borderLeft: '2px solid #0f62fe', paddingLeft: 8, fontWeight: 700, color: '#0f62fe' }}>🎯 EXEC VIEW</span>}
            <span>🔴 <strong>Cyber Incidents: 0</strong> — ERP knows nothing of tier-2 subcontractors (Nexaflow compromised){isSecurity && ' → under 2s exposure with federation'}</span>
            <span>🔴 <strong>Freight Disruptions: 0</strong> — Route data frozen at Friday 06:00 (A9/AP-7 could be closed now){isOperations && ' → 90-min reroute with satnav'}</span>
            <span>🔴 <strong>Active Suppliers: 53</strong> — Tier-1 only; 50 tier-2 subcontractors invisible{isTechnical && ' → joined via Presto federation'}</span>
          </div>

          {/* ── Two-column tables ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>

            {/* Supplier status */}
            <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 2 }}>
              <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid #e0e0e0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>Supplier Status</span>
                <span style={{ fontSize: 11, color: '#6f6f6f' }}>Source: ERP — as of {REPORT_DATE}</span>
              </div>
              {/* What this table CANNOT see — prominent callout */}
              <div style={{
                background: '#fff1f1',
                borderLeft: '4px solid #da1e28',
                borderRight: '1px solid #e0e0e0',
                borderTop: '1px solid #e0e0e0',
                borderBottom: '1px solid #e0e0e0',
                padding: '10px 14px',
                margin: '0 -1px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Warning size={14} style={{ color: '#da1e28', flexShrink: 0 }} />
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#da1e28', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    What This Table CANNOT See
                  </span>
                </div>
                <div style={{ fontSize: 11, color: '#525252', lineHeight: 1.6 }}>
                  <strong>50 tier-2 subcontractors</strong> (the companies your suppliers hire) — including <strong>Nexaflow Logistics Ltd</strong>, compromised via <strong>MOVEit (CVE-2023-34362)</strong>.
                </div>
                <div style={{ fontSize: 11, color: '#525252', lineHeight: 1.6, marginTop: 4 }}>
                  <strong>14 open POs · £47,230 exposure · 6 tier-1 suppliers affected</strong> — all invisible until a tier-1 supplier calls to say they can't deliver.
                </div>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f4f4f4' }}>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Supplier</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Region</th>
                    <th style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Open POs</th>
                    <th style={{ padding: '8px 16px', textAlign: 'center', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {SUPPLIER_DATA.map((s, i) => (
                    <tr key={s.id} style={{ borderTop: '1px solid #e0e0e0', background: i % 2 === 0 ? '#ffffff' : '#f9f9f9' }}>
                      <td style={{ padding: '10px 16px', fontWeight: 500 }}>{s.name}</td>
                      <td style={{ padding: '10px 16px', color: '#525252' }}>{s.region}</td>
                      <td style={{ padding: '10px 16px', textAlign: 'right' }}>{s.orders}</td>
                      <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                        <span style={{
                          background: '#defbe6',
                          color: '#0e6027',
                          border: '1px solid #24a148',
                          borderRadius: 8,
                          padding: '2px 8px',
                          fontSize: 10,
                          fontWeight: 700,
                        }}>
                          ● {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ padding: '8px 16px', borderTop: '1px solid #e0e0e0', fontSize: 11, color: '#8d8d8d', background: '#f4f4f4' }}>
                Tier-1 direct suppliers only. Tier-2 sub-contractors not visible in ERP.
              </div>
            </div>

            {/* Freight POs */}
            <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 2 }}>
              <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid #e0e0e0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>Active Freight POs</span>
                <span style={{ fontSize: 11, color: '#6f6f6f' }}>Source: ERP — as of {REPORT_DATE}</span>
              </div>
              {/* What this table CANNOT see — prominent callout */}
              <div style={{
                background: '#fff1f1',
                borderLeft: '4px solid #da1e28',
                borderRight: '1px solid #e0e0e0',
                borderTop: '1px solid #e0e0e0',
                borderBottom: '1px solid #e0e0e0',
                padding: '10px 14px',
                margin: '0 -1px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Warning size={14} style={{ color: '#da1e28', flexShrink: 0 }} />
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#da1e28', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    What This Table CANNOT See
                  </span>
                </div>
                <div style={{ fontSize: 11, color: '#525252', lineHeight: 1.6 }}>
                  <strong>Real-time route conditions</strong> — status based on Friday 06:00 road network snapshot.
                </div>
                <div style={{ fontSize: 11, color: '#525252', lineHeight: 1.6, marginTop: 4 }}>
                  <strong>3 POs on the A9/AP-7 corridor</strong> (Lyon→Barcelona, Lyon→Valencia, Paris→Madrid). If wildfire closes it today, you won't know until Monday's report — ship limits missed.
                </div>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f4f4f4' }}>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>PO</th>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Route</th>
                    <th style={{ padding: '8px 16px', textAlign: 'center', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>ETA</th>
                    <th style={{ padding: '8px 16px', textAlign: 'center', fontWeight: 600, color: '#525252', fontSize: 11, textTransform: 'uppercase' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {FREIGHT_DATA.map((f, i) => (
                    <tr key={f.po} style={{ borderTop: '1px solid #e0e0e0', background: i % 2 === 0 ? '#ffffff' : '#f9f9f9' }}>
                      <td style={{ padding: '10px 16px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 11 }}>{f.po}</td>
                      <td style={{ padding: '10px 16px', color: '#525252', fontSize: 11 }}>{f.route}</td>
                      <td style={{ padding: '10px 16px', textAlign: 'center' }}>{f.eta}</td>
                      <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                        <span style={{
                          background: '#defbe6',
                          color: '#0e6027',
                          border: '1px solid #24a148',
                          borderRadius: 8,
                          padding: '2px 8px',
                          fontSize: 10,
                          fontWeight: 700,
                        }}>
                          ● {f.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ padding: '8px 16px', borderTop: '1px solid #e0e0e0', fontSize: 11, color: '#8d8d8d', background: '#f4f4f4' }}>
                Route status based on Friday morning road network data. No real-time updates.
              </div>
            </div>
          </div>

          {/* ── Footer / CTA ── */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #e0e0e0',
            borderRadius: 2,
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: '#da1e28' }}>
                Report verdict: No action required — because static reports don't show what's happening now.
              </div>
              <div style={{ fontSize: 12, color: '#525252' }}>
                All KPIs green. Next report scheduled: Monday 25 Aug 2026, 06:00 BST.
                Generated from ERP data as of Friday 22 Aug 2026, 06:00 BST — 72 hours ago.
              </div>
            </div>
            <button
              onClick={() => router.push('/sources')}
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
              See the Live View →
            </button>
          </div>

          {/* ── Speaker Notes Panel (Collapsible) ── */}
          {showNotes && (
            <div style={{
              background: '#161616',
              border: '1px solid #393939',
              borderRadius: 4,
              marginTop: 24,
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
                  <span style={{ fontSize: 18, color: '#0f62fe' }}>ℹ</span>
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
                {SPEAKER_NOTES.map((note, idx) => (
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
