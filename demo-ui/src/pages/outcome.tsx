/**
 * Page 3 — "The Outcome"
 * Redesigned comparison section: horizontal "time to action" bars make the
 * speed difference viscerally obvious before the reader processes any text.
 */

import Head from 'next/head'
import { useRouter } from 'next/router'

// ── Timeline bar data ─────────────────────────────────────────────────────────
// Each scenario has an old-world and new-world track.
// `slots` are evenly spaced left-to-right. `actionAt` index = when action lands.
// `endLabel` = what happened at the end of the bar.

const CYBER_OLD = {
  label: 'Old world — Static report',
  color: '#da1e28',
  bgColor: '#fff1f1',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated', type: 'start' },
    { time: 'Fri–Sun',   event: 'Breach escalates undetected', type: 'bad' },
    { time: 'Mon 08:30', event: 'Supplier calls to say they can\'t fulfil', type: 'bad' },
    { time: 'Mon 11:00', event: 'Exposure confirmed: £47,230', type: 'bad' },
    { time: 'Mon 14:00', event: 'Alternative supplier found', type: 'bad' },
    { time: 'Tue–Wed',   event: '3 SLA breaches. £8,400 expediting costs.', type: 'cost' },
  ],
  actionAt: 4, // "alternative supplier found" = first real action
  cost: '£15,200',
  costLabel: 'SLA breaches + expediting + emergency premium',
  timeToAction: '~80 hours',
}

const CYBER_NEW = {
  label: 'New world — watsonx.data federation',
  color: '#24a148',
  bgColor: '#defbe6',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated', type: 'start' },
    { time: 'Fri 11:14', event: 'Threat intelligence signal ingested to Iceberg', type: 'alert' },
    { time: 'Fri 11:14', event: 'Federated detection: IBM i × EDB × Threat Feed in <2s', type: 'action' },
    { time: 'Fri 11:30', event: 'Alternative supplier pre-qualified', type: 'action' },
    { time: 'Fri 14:00', event: '11 of 14 POs re-routed. SLAs protected.', type: 'saved' },
  ],
  actionAt: 2,
  cost: '£1,200',
  costLabel: 'Rerouting admin only — SLA breaches: 0',
  timeToAction: '~5 hours',
}

const WILDFIRE_OLD = {
  label: 'Old world — Static report',
  color: '#da1e28',
  bgColor: '#fff1f1',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated — all routes clear', type: 'start' },
    { time: 'Mon 06:00', event: 'Wildfire closes A9/AP-7 corridor', type: 'bad' },
    { time: 'Mon–Wed',   event: '3 missed ship limits. No visibility.', type: 'bad' },
    { time: 'Wed 10:00', event: 'Rerouting finally arranged', type: 'bad' },
    { time: 'Thu',       event: '2 SLA breaches. £6,800 expediting.', type: 'cost' },
    { time: 'Fri+7',     event: 'Next report reflects last week\'s disruption', type: 'cost' },
  ],
  actionAt: 3,
  cost: '£8,700',
  costLabel: '2 SLA breaches + expediting + stock transfer',
  timeToAction: '~96 hours',
}

const WILDFIRE_NEW = {
  label: 'New world — watsonx.data federation',
  color: '#24a148',
  bgColor: '#defbe6',
  slots: [
    { time: 'Mon 06:00', event: 'Route Disruption feed signals A9/AP-7 closure', type: 'alert' },
    { time: 'Mon 06:02', event: 'Signal ingested → federated detector runs in <2s', type: 'action' },
    { time: 'Mon 06:15', event: 'On-call manager alerted, rerouting pre-approved', type: 'action' },
    { time: 'Mon 07:30', event: '5 of 7 POs rerouted before business day starts', type: 'saved' },
    { time: 'Mon EOD',   event: 'SLA breaches: 0. Stockouts: 0.', type: 'saved' },
  ],
  actionAt: 1,
  cost: '£1,900',
  costLabel: 'Rerouting admin only — SLA breaches: 0',
  timeToAction: '~90 minutes',
}

// ── Shared Power pillars (appear on both outcome pages) ───────────────────────

const PILLAR_IBMI = {
  icon: '⚙',
  colour: '#4589ff',
  title: 'IBM i — The ERP runs here',
  subtitle: 'Source 1 is a real IBM Power LPAR',
  points: [
    'Your core transactional data lives on IBM i — 99k+ orders, 32k products, real Db2 for i.',
    'watsonx.data federates directly to Db2 for IBM i via the native connector — no ETL, no copy.',
    'This is the data your ERP has always had. Federation makes it joinable with the sources it couldn\'t see.',
    'Running IBM i alongside a modern lakehouse is often news to audiences — it\'s not legacy, it\'s an asset.',
  ],
}

const PILLAR_MMA = {
  icon: '⚡',
  colour: '#08bdba',
  title: 'Real-Time Federation & AI Readiness on Power',
  subtitle: 'Immediate cross-system joins with built-in Matrix Math Acceleration',
  points: [
    'Continuous detection and queries run on RHEL on IBM Power — genuine Power hardware.',
    'Federation links IBM i ERP and operational databases in seconds, turning passive reporting into immediate operational response.',
    'Teams can react manually or automate actions before business operations are disrupted.',
    'IBM Power\'s Matrix Math Accelerator (MMA) enables optional on-box AI risk scoring and pattern matching without expensive GPU clusters.',
  ],
}

const PILLAR_CYBER = {
  icon: '🔒',
  colour: '#be95ff',
  title: 'IBM Power — Reduced Attack Surface',
  subtitle: 'Security posture built into the architecture',
  points: [
    'IBM i\'s object-based memory architecture means common exploit vectors — buffer overflows, code injection — simply don\'t work.',
    'Running your ERP on IBM Power isn\'t just a performance choice. It\'s a security posture that shrinks the blast radius of supply chain attacks like this one.',
    'PowerSC provides continuous security monitoring and compliance scoring for IBM Power workloads — built-in, not bolted-on.',
    'One vendor conversation. IBM owns the ERP, the hardware, the lakehouse, and the security layer.',
  ],
}

const PILLAR_HYBRID = {
  icon: '☁',
  colour: '#be95ff',
  title: 'IBM Power — Hybrid Cloud Continuity',
  subtitle: 'On-prem resilience + cloud flexibility',
  points: [
    'IBM Power\'s hybrid cloud flexibility means your ERP and operational data can span on-prem and IBM Cloud.',
    'When a physical region is disrupted — road closure, wildfire, flooding — workloads can be moved without re-platforming.',
    'The data your watsonx.data federation queries doesn\'t have to be at risk just because a logistics corridor is.',
    'IBM Power + IBM Cloud: the same ISA, the same operating model, the same security posture — wherever the workload needs to run.',
  ],
}

const POWER_PILLARS: Record<'cyber' | 'wildfire', typeof PILLAR_IBMI[]> = {
  cyber:    [PILLAR_IBMI, PILLAR_MMA, PILLAR_CYBER],
  wildfire: [PILLAR_IBMI, PILLAR_MMA, PILLAR_HYBRID],
}

// ── Horizontal timeline bar component ─────────────────────────────────────────

type Slot = { time: string; event: string; type: string }
type Track = {
  label: string; color: string; bgColor: string
  slots: Slot[]; actionAt: number
  cost: string; costLabel: string; timeToAction: string
  // Optional: unix-like numeric time values for proportional positioning.
  // If omitted, slots are evenly spaced.
  timeValues?: number[]
}

// Convert the qualitative time strings into a numeric value (minutes from Fri 00:00)
// so the "before" bar spanning days looks dramatically longer than the "after" bar.
function toMinutes(t: string): number {
  const lower = t.toLowerCase().trim()

  // Day-name → base minutes from Fri 00:00
  const DAY: Record<string, number> = {
    fri: 0, sat: 24 * 60, sun: 48 * 60,
    mon: 72 * 60, tue: 96 * 60, wed: 120 * 60, thu: 144 * 60,
  }

  // "Fri+7" → next Friday (7 days after the origin Fri)
  if (/fri\+7/.test(lower)) return 7 * 24 * 60

  // "Mon EOD" → end of that day
  if (/eod/.test(lower)) {
    const dayMatch = lower.match(/^(fri|sat|sun|mon|tue|wed|thu)/)
    return (dayMatch ? (DAY[dayMatch[1]] ?? 0) : 0) + 23 * 60
  }

  // "Fri–Sun", "Mon–Wed", "Tue–Wed" → midpoint of range
  const rangeMatch = lower.match(/^(fri|sat|sun|mon|tue|wed|thu)[–\-](fri|sat|sun|mon|tue|wed|thu)/)
  if (rangeMatch) {
    const a = DAY[rangeMatch[1]] ?? 0
    const b = DAY[rangeMatch[2]] ?? 0
    return (a + b) / 2
  }

  // "Mon 06:00", "Fri 11:14" → day + HH:MM
  const timeMatch = lower.match(/^(fri|sat|sun|mon|tue|wed|thu)\s+(\d{1,2}):(\d{2})/)
  if (timeMatch) {
    return (DAY[timeMatch[1]] ?? 0) + parseInt(timeMatch[2]) * 60 + parseInt(timeMatch[3])
  }

  // bare day name "Thu", "Mon"
  const bareMatch = lower.match(/^(fri|sat|sun|mon|tue|wed|thu)$/)
  if (bareMatch) return DAY[bareMatch[1]] ?? 0

  return 0
}

// Return 0–100% positions for each slot on a SHARED scale (scaleMin..scaleMax).
// Inset slightly so first/last dots are never clipped by the container edge.
const DOT_MARGIN = 2 // % inset from each edge
function slotPositions(slots: Slot[], scaleMin: number, scaleMax: number): number[] {
  const span = scaleMax - scaleMin || 1
  return slots.map(s => {
    const v = toMinutes(s.time)
    return DOT_MARGIN + ((v - scaleMin) / span) * (100 - 2 * DOT_MARGIN)
  })
}

function TimelineBar({ track, isOld, scaleMin, scaleMax }: {
  track: Track; isOld: boolean; scaleMin: number; scaleMax: number
}) {
  const positions = slotPositions(track.slots, scaleMin, scaleMax)
  const actionPct = positions[track.actionAt]
  const firstPct  = positions[0]

  return (
    <div style={{ marginBottom: 8 }}>
      {/* Label row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
          letterSpacing: '0.06em', color: track.color,
        }}>
          {isOld ? '❌' : '✓'} {track.label}
        </span>
      </div>

      {/* The bar — clean numbered dots, no text on the bar itself */}
      <div style={{ position: 'relative', height: 30 }}>
        {/* Background track */}
        <div style={{
          position: 'absolute',
          top: 12,
          left: `${DOT_MARGIN}%`,
          right: `${DOT_MARGIN}%`,
          height: 6,
          background: '#e0e0e0',
          borderRadius: 3,
        }} />

        {/* Filled portion — coloured region shows the "cost of waiting" gap:
            - Old world:  red  from first dot → action dot  (the long wait)
            - New world:  green from left edge → action dot (the short reaction time)
            Both fill to actionAt so the bar lengths are directly comparable. */}
        {(() => {
          const fillStart = isOld ? firstPct : DOT_MARGIN
          const fillEnd   = actionPct
          const minWidth  = 2
          return (
            <div style={{
              position: 'absolute',
              top: 12,
              left: `${fillStart}%`,
              width: `${Math.max(minWidth, fillEnd - fillStart)}%`,
              height: 6,
              background: isOld ? '#ffb3b8' : '#a7f0ba',
              borderRadius: 3,
            }} />
          )
        })()}

        {/* Numbered dots — no text, just the badge */}
        {track.slots.map((slot, i) => {
          const pct = positions[i]
          const isAction = i === track.actionAt
          const isPast = i < track.actionAt
          const dotColor = isAction
            ? track.color
            : isPast ? (isOld ? '#ffb3b8' : '#a7f0ba') : '#e0e0e0'
          const dotSize = isAction ? 16 : 10
          const numColor = isAction ? '#fff' : (isPast ? (isOld ? '#da1e28' : '#24a148') : '#a8a8a8')

          return (
            <div key={i} style={{
              position: 'absolute',
              left: `${pct}%`,
              top: isAction ? 4 : 7,
              transform: 'translateX(-50%)',
              width: dotSize,
              height: dotSize,
              borderRadius: '50%',
              background: dotColor,
              border: isAction ? `2px solid ${track.color}` : `1px solid ${isOld ? '#e8a0a4' : '#74c69d'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2,
              flexShrink: 0,
            }}>
              <span style={{ fontSize: 7, fontWeight: 700, color: numColor, lineHeight: 1 }}>
                {i + 1}
              </span>
            </div>
          )
        })}
      </div>

      {/* Legend — one column per slot, matches dot count exactly, never wraps */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${track.slots.length}, 1fr)`,
        gap: '3px 8px',
        marginTop: 8,
      }}>
        {track.slots.map((slot, i) => {
          const isAction = i === track.actionAt
          return (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 5,
              fontSize: 10,
              lineHeight: 1.4,
            }}>
              {/* Number badge */}
              <div style={{
                flexShrink: 0,
                width: 14,
                height: 14,
                borderRadius: '50%',
                background: isAction ? track.color : '#e0e0e0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginTop: 1,
              }}>
                <span style={{ fontSize: 7, fontWeight: 700, color: isAction ? '#fff' : '#6f6f6f', lineHeight: 1 }}>
                  {i + 1}
                </span>
              </div>
              {/* Timestamp + event */}
              <div>
                <span style={{
                  fontFamily: 'IBM Plex Mono, monospace',
                  fontSize: 9,
                  color: isAction ? track.color : '#6f6f6f',
                  fontWeight: isAction ? 700 : 400,
                  display: 'block',
                  lineHeight: 1.2,
                }}>
                  {slot.time === 'Fri+7' ? 'Fri (next week)' : slot.time}
                  {isAction && <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.05em', marginLeft: 4 }}>⚡ action</span>}
                </span>
                <span style={{
                  color: isAction ? track.color : '#525252',
                  fontWeight: isAction ? 600 : 400,
                }}>
                  {slot.event}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Time-to-action + cost callout */}
      <div style={{
        marginTop: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '6px 12px',
        background: track.bgColor,
        border: `1px solid ${track.color}44`,
        borderLeft: `3px solid ${track.color}`,
        borderRadius: 2,
      }}>
        <div>
          <span style={{ fontSize: 10, color: '#6f6f6f', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Time to action </span>
          <span style={{ fontSize: 16, fontWeight: 700, color: track.color }}>{track.timeToAction}</span>
        </div>
        <div style={{ width: 1, height: 28, background: '#e0e0e0' }} />
        <div>
          <span style={{ fontSize: 10, color: '#6f6f6f', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total cost </span>
          <span style={{ fontSize: 16, fontWeight: 700, color: track.color }}>{track.cost}</span>
          <span style={{ fontSize: 10, color: '#6f6f6f', marginLeft: 6 }}>{track.costLabel}</span>
        </div>
      </div>
    </div>
  )
}

function ScenarioBlock({ title, oldTrack, newTrack, saving, savingLabel, scaleOrigin }: {
  title: string; oldTrack: Track; newTrack: Track; saving: string; savingLabel: string
  // Optional override for scaleMin — lets both bars share a common anchor
  // other than the old-world first slot (needed when old/new worlds start at different times).
  scaleOrigin?: number
}) {
  // Both bars share the same time scale so the new-world bar appears visually
  // compressed — its dots cluster in the left fraction of the track.
  const oldTimes = oldTrack.slots.map(s => toMinutes(s.time))
  const allTimes = [...oldTimes, ...newTrack.slots.map(s => toMinutes(s.time))]
  const scaleMin = scaleOrigin ?? Math.min(...allTimes)
  const scaleMax = Math.max(...oldTimes) // old-world always sets the far end

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 2, overflow: 'hidden' }}>
      {/* Scenario header with saving callout */}
      <div style={{
        padding: '12px 20px',
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        background: '#f9f9f9',
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#161616', flex: 1 }}>
          {title}
        </div>
        {/* Saving badge */}
        <div style={{
          background: '#defbe6', border: '1px solid #24a148',
          borderRadius: 2, padding: '4px 14px',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ fontSize: 10, color: '#0e6027', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Potential saving</span>
          <span style={{ fontSize: 20, fontWeight: 700, color: '#0e6027' }}>{saving}</span>
          <span style={{ fontSize: 10, color: '#0e6027' }}>{savingLabel}</span>
        </div>
      </div>

      {/* Stacked tracks — both drawn on the same time scale */}
      <div>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e0e0e0' }}>
          <TimelineBar track={oldTrack} isOld={true} scaleMin={scaleMin} scaleMax={scaleMax} />
        </div>
        <div style={{ padding: '16px 20px' }}>
          <TimelineBar track={newTrack} isOld={false} scaleMin={scaleMin} scaleMax={scaleMax} />
        </div>
      </div>
    </div>
  )
}

// Force SSR so router.query (scenario param) is available on first render
export const getServerSideProps = () => ({ props: {} })

export default function OutcomePage() {
  const router = useRouter()
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
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 24" width="42" height="17" aria-label="IBM">
            <path fill="#1192e8" d="M0 18.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm13 13.5h26v-2H13v2zm4-4.5h18v-2H17v2zm0-4.5h18v-2H17v2zm-4-4.5h26v-2H13v2zm30 13.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2z"/>
          </svg>
          <span style={{ fontWeight: 700, fontSize: 14, color: '#f4f4f4' }}>watsonx.data on IBM Power</span>
          <span style={{ fontSize: 12, color: '#8d8d8d', borderLeft: '1px solid #393939', paddingLeft: 16 }}>The Outcome</span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 11, color: '#6f6f6f' }}>{breadcrumb}</span>
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

          {/* ── Section 1: Time to action ── */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#525252', marginBottom: 8 }}>
              What happened next
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
              <strong>The data was always there.</strong> The gap wasn't information — it was time and joinability.
              A static report cannot ask a question that spans three systems. watsonx.data can.
              On IBM Power, it does it in under 2 seconds.
            </div>
          </div>

          {/* ── Section 2: Why IBM Power (scenario-specific third pillar) ── */}
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

            {/* Close / next CTA */}
            <div style={{
              marginTop: 20, background: '#161616', borderRadius: 2,
              padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 24,
            }}>
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
          </div>

        </div>
      </div>
    </>
  )
}
