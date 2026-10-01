/**
 * Page 3 — "The Outcome"
 * Horizontal "time to action" bars make the speed difference viscerally obvious.
 *
 * Data constants → outcome-data.ts
 * Timeline bar components → OutcomeTimeline.tsx
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { HeaderName } from '@carbon/react'
import { useAudience } from '../context/AudienceContext'
import {
  CYBER_OLD, CYBER_NEW, WILDFIRE_OLD, WILDFIRE_NEW, POWER_PILLARS,
} from '../components/outcome-data'
import { ScenarioBlock, toMinutes } from '../components/OutcomeTimeline'

// Force SSR so router.query (scenario param) is available on first render
export const getServerSideProps = () => ({ props: {} })

export default function OutcomePage() {
  const router = useRouter()
  const { isSecurity, isTechnical, isExecutive, isOperations } = useAudience()
  if (!router.isReady) return null
  const scenario = (router.query.scenario as string) === 'wildfire' ? 'wildfire' : 'cyber'
  const isCyber = scenario === 'cyber'
  const pillars = POWER_PILLARS[scenario]

  const timelineTitle    = isCyber ? 'Scenario 1 — Supplier Cyber Incident'  : 'Scenario 2 — EU Wildfire Road Closure'
  const timelineSaving   = isCyber ? '£14,000' : '£6,800'
  const closingCTA       = isCyber
    ? { label: 'Run Scenario 2 — Wildfire →', href: '/live?scenario=wildfire' }
    : { label: 'Start again →',                href: '/' }
  const backHref         = isCyber ? '/live?scenario=cyber' : '/live?scenario=wildfire'
  const breadcrumb       = isCyber ? '③ Cyber outcome' : '⑤ Wildfire outcome'

  return (
    <>
      <Head>
        <title>The Outcome — {timelineTitle} — watsonx.data on IBM Power</title>
      </Head>

      <div style={{
        minHeight: '100vh',
        background: '#f4f4f4',
        fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
        color: '#161616',
      }}>

        {/* Header */}
        <div style={{
          background: '#161616', borderBottom: '1px solid #393939',
          padding: '0 32px', display: 'flex', alignItems: 'center', height: 56, gap: 16,
        }}>
          <HeaderName prefix="IBM" href="/" style={{ paddingLeft: 0, textDecoration: 'none' }}>
            watsonx.data on IBM Power
          </HeaderName>
          <span style={{ fontSize: 12, color: '#8d8d8d', borderLeft: '1px solid #393939', paddingLeft: 16 }}>The Outcome</span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 11, color: '#6f6f6f' }}>{breadcrumb}</span>
          {(isSecurity || isTechnical || isExecutive || isOperations) && (
            <span style={{
              background: '#1e1e1e',
              border: '1px solid #393939',
              borderRadius: 12,
              padding: '3px 10px',
              fontSize: 10,
              fontWeight: 600,
              color: isSecurity ? '#da1e28' : isTechnical ? '#a855f7' : isOperations ? '#24a148' : '#0f62fe',
              textTransform: 'uppercase',
            }}>
              {isSecurity && '🔒 SEC VIEW'}
              {isTechnical && '🔧 TECH VIEW'}
              {isOperations && '📦 OPS VIEW'}
              {isExecutive && '🎯 EXEC VIEW'}
            </span>
          )}
          <button onClick={() => router.push(backHref)}
            style={{ background: 'transparent', border: '1px solid #525252', color: '#c6c6c6', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            ← Live view
          </button>
          <button onClick={() => router.push('/')}
            style={{ background: 'transparent', border: '1px solid #525252', color: '#c6c6c6', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            ⟳ Start again
          </button>
        </div>

        <div style={{ padding: '28px 32px', maxWidth: 1280, margin: '0 auto' }}>

          {/* ── Hero Metrics Row: Time-to-Action & Cost Avoidance ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
            <div style={{ background: '#fff1f1', border: '2px solid #da1e28', borderRadius: 4, padding: '24px', textAlign: 'center', position: 'relative' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#da1e28', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Static Report</div>
              <div style={{ fontSize: 48, fontWeight: 700, color: '#da1e28', lineHeight: 1, marginBottom: 4 }}>{isCyber ? '80 hrs' : '96 hrs'}</div>
              <div style={{ fontSize: 13, color: '#525252' }}>Time to Action</div>
              <div style={{ fontSize: 11, color: '#da1e28', marginTop: 8, fontWeight: 600 }}>Cost: {isCyber ? '£15,200' : '£8,700'}</div>
              {isSecurity && <div style={{ position: 'absolute', top: 8, right: 8, background: '#da1e28', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}><span>🔒 SEC</span></div>}
            </div>
            <div style={{ background: '#defbe6', border: '2px solid #24a148', borderRadius: 4, padding: '24px', textAlign: 'center', position: 'relative' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#24a148', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Live Federation (Satnav)</div>
              <div style={{ fontSize: 48, fontWeight: 700, color: '#24a148', lineHeight: 1, marginBottom: 4 }}>{isCyber ? '5 hrs' : '1.5 hrs'}</div>
              <div style={{ fontSize: 13, color: '#525252' }}>Time to Action</div>
              <div style={{ fontSize: 11, color: '#24a148', marginTop: 8, fontWeight: 600 }}>Cost: {isCyber ? '£1,200' : '£1,900'}</div>
              {isOperations && <div style={{ position: 'absolute', top: 8, right: 8, background: '#24a148', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}><span>📦 OPS</span></div>}
            </div>
            <div style={{ background: '#fef3c7', border: '2px solid #f1c21b', borderRadius: 4, padding: '24px', textAlign: 'center', position: 'relative' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#b8860b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Potential Saving</div>
              <div style={{ fontSize: 48, fontWeight: 700, color: '#b8860b', lineHeight: 1, marginBottom: 4 }}>{isCyber ? '£14,000' : '£6,800'}</div>
              <div style={{ fontSize: 13, color: '#525252' }}>Cost Avoidance</div>
              <div style={{ fontSize: 11, color: '#b8860b', marginTop: 8, fontWeight: 600 }}>{isCyber ? '92% reduction' : '78% reduction'}</div>
              {isExecutive && <div style={{ position: 'absolute', top: 8, right: 8, background: '#0f62fe', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}><span>🎯 EXEC</span></div>}
            </div>
            <div style={{ background: '#e8f4ff', border: '2px solid #0f62fe', borderRadius: 4, padding: '24px', textAlign: 'center', position: 'relative' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#0f62fe', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Speedup Factor</div>
              <div style={{ fontSize: 48, fontWeight: 700, color: '#0f62fe', lineHeight: 1, marginBottom: 4 }}>{isCyber ? '16×' : '64×'}</div>
              <div style={{ fontSize: 13, color: '#525252' }}>Faster Response</div>
              <div style={{ fontSize: 11, color: '#0f62fe', marginTop: 8, fontWeight: 600 }}>{isCyber ? 'SLAs: 0 breaches' : 'Stockouts: 0'}</div>
              {isTechnical && <div style={{ position: 'absolute', top: 8, right: 8, background: '#a855f7', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}><span>🔧 TECH</span></div>}
            </div>
          </div>

          {/* ── Business Actions Enabled ── */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#525252', marginBottom: 12 }}>
              What This Enables — Business Actions in Minutes, Not Days {isSecurity && '(SEC)'} {isTechnical && '(TECH)'} {isOperations && '(OPS)'} {isExecutive && '(EXEC)'}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              {isCyber ? (
                <>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ 11 of 14 POs Re-routed</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>Before the breach disrupted supply, alternative tier-2 suppliers pre-qualified and POs redirected — while the event was still unfolding.</div>
                    {isSecurity && <div style={{ position: 'absolute', top: 8, right: 8, background: '#da1e28', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🔒 SEC</div>}
                    {isOperations && <div style={{ position: 'absolute', top: 8, right: 8, background: '#24a148', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>📦 OPS</div>}
                  </div>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ 0 SLA Breaches</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>Customer delivery commitments protected. No penalty clauses triggered. No emergency expediting fees.</div>
                    {isSecurity && <div style={{ position: 'absolute', top: 8, right: 8, background: '#da1e28', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🔒 SEC</div>}
                    {isExecutive && <div style={{ position: 'absolute', top: 8, right: 8, background: '#0f62fe', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🎯 EXEC</div>}
                  </div>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ £14K Cost Avoided</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>vs £15.2K in the static report world (SLA penalties, expediting, emergency premiums).</div>
                    {isExecutive && <div style={{ position: 'absolute', top: 8, right: 8, background: '#0f62fe', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🎯 EXEC</div>}
                  </div>
                </>
              ) : (
                <>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ 5 of 7 POs Re-routed</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>Before business day starts, freight redirected around A9/AP-7 closure via Alpine passes — pre-approved by on-call manager.</div>
                    {isOperations && <div style={{ position: 'absolute', top: 8, right: 8, background: '#24a148', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>📦 OPS</div>}
                  </div>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ 0 Stockouts</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>Demand spike on key SKUs detected in real-time POS stream — inventory rebalanced before shelves emptied.</div>
                    {isOperations && <div style={{ position: 'absolute', top: 8, right: 8, background: '#24a148', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>📦 OPS</div>}
                    {isTechnical && <div style={{ position: 'absolute', top: 8, right: 8, background: '#a855f7', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🔧 TECH</div>}
                  </div>
                  <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderLeft: '4px solid #24a148', borderRadius: 2, padding: '16px', position: 'relative' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#24a148', marginBottom: 8 }}>✓ £6.8K Cost Avoided</div>
                    <div style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>vs £8.7K in the static report world (expediting, stock transfers, lost sales).</div>
                    {isExecutive && <div style={{ position: 'absolute', top: 8, right: 8, background: '#0f62fe', color: '#fff', fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 2, textTransform: 'uppercase' }}>🎯 EXEC</div>}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ── Section 1: Time to action (timeline comparison) ── */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#525252', marginBottom: 8 }}>
              What happened next — timeline comparison
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 4px', color: '#161616' }}>
              The cost of waiting for the next report
            </h2>
            <p style={{ fontSize: 13, color: '#525252', margin: '0 0 20px', lineHeight: 1.6 }}>
              Same event. Same data. The difference is entirely <strong>time to action</strong> —
              determined by whether your systems can join across the gap in real time,
              or wait for the next scheduled report.
            </p>

            <div style={{ marginBottom: 16 }}>
              {isCyber ? (
                <ScenarioBlock
                  title={timelineTitle}
                  oldTrack={CYBER_OLD}
                  newTrack={CYBER_NEW}
                  saving={timelineSaving}
                  savingLabel="saved vs old world"
                />
              ) : (
                <ScenarioBlock
                  title={timelineTitle}
                  oldTrack={WILDFIRE_OLD}
                  newTrack={WILDFIRE_NEW}
                  saving={timelineSaving}
                  savingLabel="saved vs old world"
                  scaleOrigin={toMinutes('Mon 06:00')}
                />
              )}
            </div>

            <div style={{
              background: '#e8f4ff', border: '1px solid #4589ff',
              borderLeft: '4px solid #0f62fe', borderRadius: 2,
              padding: '12px 20px', fontSize: 13, color: '#0043ce',
            }}>
              <strong>The data was always there.</strong> The gap wasn&apos;t information — it was time and joinability.
              A static report cannot ask a question that spans three systems. watsonx.data can.
              On IBM Power, it does it in under 2 seconds.
            </div>
          </div>

          {/* ── Section 2: Why IBM Power ── */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#525252', marginBottom: 8 }}>
              Why IBM Power
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 4px', color: '#161616' }}>
              The platform that made it possible
            </h2>
            <p style={{ fontSize: 13, color: '#525252', margin: '0 0 20px' }}>
              Every component of this demo ran on IBM Power hardware — not cloud, not x86. Here is why that matters
              {isCyber ? ' for cyber resilience.' : ' for logistics continuity.'}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              {pillars.map((p) => (
                <div key={p.title} style={{
                  background: '#ffffff', border: '1px solid #e0e0e0',
                  borderTop: `4px solid ${p.colour}`, borderRadius: 2, padding: '20px',
                }}>
                  <div style={{ fontSize: 28, marginBottom: 12 }}>{p.icon}</div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: '#161616', marginBottom: 4 }}>{p.title}</div>
                  <div style={{ fontSize: 11, color: p.colour, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 12 }}>
                    {p.subtitle}
                  </div>
                  <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {p.points.map((pt, i) => (
                      <li key={i} style={{ fontSize: 12, color: '#525252', lineHeight: 1.5 }}>{pt}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Closing Verdict + Audience-Specific Next Steps */}
            <div style={{
              marginTop: 20, background: '#161616', borderRadius: 2,
              padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#f4f4f4', marginBottom: 6 }}>
                    IBM i runs your ERP. IBM Power runs the intelligence that watches over it.
                  </div>
                  <div style={{ fontSize: 12, color: '#8d8d8d', lineHeight: 1.6 }}>
                    {isCyber
                      ? 'The breach was always going to happen. The question is whether you find out in 5 hours or 80.'
                      : 'The road was always going to close. The question is whether you act in 90 minutes or 4 days.'}
                  </div>
                </div>
                <button onClick={() => router.push(closingCTA.href)} style={{
                  background: '#0f62fe', color: '#fff', border: 'none', borderRadius: 2,
                  padding: '12px 24px', fontSize: 13, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                }}>
                  {closingCTA.label}
                </button>
              </div>

              {/* Audience-Specific Next Steps — Collapsible */}
              <details style={{ border: '1px solid #393939', borderRadius: 2, overflow: 'hidden' }}>
                <summary style={{
                  padding: '12px 16px', background: '#1e1e1e', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 12,
                  fontSize: 12, fontWeight: 600, color: '#f4f4f4',
                  userSelect: 'none', listStyle: 'none',
                }}>
                  <span style={{ color: '#08bdba' }}>▸</span>
                  <span>Next steps for your role →</span>
                  <span style={{ marginLeft: 'auto', fontSize: 10, color: '#8d8d8d', textTransform: 'uppercase' }}>
                    Tailor the conversation
                  </span>
                </summary>
                <div style={{ padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                  {/* CISO / Security */}
                  <div style={{ background: '#0a1a2a', border: '1px solid #1d4ed8', borderRadius: 2, padding: '12px' }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#4589ff', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                      🔒 CISO / Security Leader
                    </div>
                    <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: 11, color: '#c6c6c6', lineHeight: 1.7, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <li>Map your tier-2 attack surface — federation reveals suppliers your ERP cannot see</li>
                      <li>Continuous threat feed ingestion → auto-enrichment with supplier graph → SIEM ticket (QRadar/Splunk)</li>
                      <li>PowerSC continuous compliance scoring built-in — reduce audit prep from weeks to days</li>
                      <li>Single vendor accountability: ERP + hardware + lakehouse + security layer</li>
                    </ul>
                  </div>
                  {/* Data Architect */}
                  <div style={{ background: '#1a0a2a', border: '1px solid #7e22ce', borderRadius: 2, padding: '12px' }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#a855f7', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                      🏗 Data Architect / Engineer
                    </div>
                    <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: 11, color: '#c6c6c6', lineHeight: 1.7, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <li>Zero-ETL federated Presto across IBM i (Db2) + PostgreSQL + Iceberg — under 2s query latency</li>
                      <li>Kafka/Flink stream processor → normalised signal topic → auto-triggers same federation query → Iceberg sink</li>
                      <li>MMA on-box acceleration for optional AI risk scoring — no GPU cluster, no data egress</li>
                      <li>Iceberg on COS: time-travel, schema evolution, ACID — open table format, no lock-in</li>
                    </ul>
                  </div>
                  {/* Supply-Chain / Procurement */}
                  <div style={{ background: '#0a2a0a', border: '1px solid #24a148', borderRadius: 2, padding: '12px' }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#24a148', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                      📦 Supply-Chain / Procurement
                    </div>
                    <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: 11, color: '#c6c6c6', lineHeight: 1.7, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <li>Real-time exposure visibility: which POs, which customers, how much £ — before shipment</li>
                      <li>Route feed webhook → warehouse corridor match → PagerDuty alert to on-call manager in seconds</li>
                      <li>Pre-qualify alternative suppliers with full exposure list in minutes, not days</li>
                      <li>Protect SLAs &amp; avoid stockouts — reroute freight before the business day starts</li>
                    </ul>
                  </div>
                  {/* IT Director / C-suite */}
                  <div style={{ background: '#2a1a0a', border: '1px solid #f1c21b', borderRadius: 2, padding: '12px' }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#f1c21b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                      🎯 IT Director / C-Suite
                    </div>
                    <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: 11, color: '#c6c6c6', lineHeight: 1.7, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <li>Operational resilience: 16–64× faster response turns £15K incidents into £1K admin</li>
                      <li>Managed ingestion pipeline on OpenShift → watsonx.data federation → ServiceNow workflow</li>
                      <li>Workload mobility without re-platforming: same ISA, same model, same security — on-prem or cloud</li>
                      <li>One vendor conversation. IBM owns the stack. One throat to choke.</li>
                    </ul>
                  </div>
                </div>
              </details>
            </div>

          </div>
        </div>
      </div>
    </>
  )
}
