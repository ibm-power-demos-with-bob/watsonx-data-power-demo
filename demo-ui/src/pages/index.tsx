/**
 * Page 1 — "The Static Map"
 *
 * A mock weekly management report, last generated Friday 06:00.
 * Everything looks fine. Suppliers green. Freight on track.
 * This is the "before" state — the world as the business believes it is.
 *
 * Presenter script:
 * "This is what your business looks like based on your last report.
 *  Generated Friday morning at 6am. It's now Monday. Nothing unusual —
 *  all suppliers active, all freight on track, no flags.
 *  [pause]
 *  Let me show you what was actually happening."
 */

import Head from 'next/head'
import { useRouter } from 'next/router'

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

export default function StaticMapPage() {
  const router = useRouter()

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
          {/* IBM logo */}
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 24" width="42" height="17" aria-label="IBM">
            <path fill="#0f62fe" d="M0 18.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm13 13.5h26v-2H13v2zm4-4.5h18v-2H17v2zm0-4.5h18v-2H17v2zm-4-4.5h26v-2H13v2zm30 13.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2z"/>
          </svg>
          <span style={{ fontWeight: 700, fontSize: 14, color: '#161616' }}>Supply Chain Operations</span>
          <span style={{ fontSize: 12, color: '#525252', borderLeft: '1px solid #e0e0e0', paddingLeft: 16 }}>
            Weekly Management Report
          </span>
          <div style={{ flex: 1 }} />
          {/* Stale timestamp — the whole point */}
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: '#6f6f6f' }}>Report generated</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#525252' }}>{REPORT_DATE}</div>
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
        </div>

        <div style={{ padding: '24px 32px', maxWidth: 1280, margin: '0 auto' }}>

          {/* ── Viewed-at warning — subtle ── */}
          <div style={{
            background: '#fff8e1',
            border: '1px solid #f1c21b',
            borderRadius: 2,
            padding: '8px 16px',
            marginBottom: 24,
            fontSize: 12,
            color: '#6f6f6f',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{ fontSize: 14 }}>🕐</span>
            You are viewing a report generated <strong>3 days ago</strong>. Last refreshed: {REPORT_DATE}. Viewing at: {VIEWED_DATE}.
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
              }}>
                <div style={{ fontSize: 11, color: '#6f6f6f', marginBottom: 4 }}>{k.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#161616', lineHeight: 1 }}>{k.value}</div>
                <div style={{ fontSize: 11, color: '#24a148', marginTop: 4 }}>↑ {k.sub}</div>
              </div>
            ))}
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
                ⚠ Note: This report shows tier-1 direct suppliers only. Tier-2 sub-contractors are not visible in ERP.
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
                ⚠ Note: Route status based on Friday morning road network data. No real-time updates.
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
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                Report summary: No action required.
              </div>
              <div style={{ fontSize: 12, color: '#525252' }}>
                All KPIs within normal range. Next report scheduled: Monday 25 Aug 2026, 06:00 BST.
                This report was generated from ERP data as of Friday 22 Aug 2026, 06:00 BST.
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
              See the Live Federation Architecture →
            </button>
          </div>

        </div>
      </div>
    </>
  )
}
