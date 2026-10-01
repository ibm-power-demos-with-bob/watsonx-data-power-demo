/**
 * OutcomeTimeline.tsx — timeline rendering components for the Outcome page.
 * Extracted from outcome.tsx to keep the page file manageable.
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export type Slot = { time: string; event: string; type: string }
export type Track = {
  label: string; color: string; bgColor: string
  slots: Slot[]; actionAt: number
  cost: string; costLabel: string; timeToAction: string
  timeValues?: number[]
}

// ── Time helpers ──────────────────────────────────────────────────────────────

// Convert the qualitative time strings into a numeric value (minutes from Fri 00:00)
// so the "before" bar spanning days looks dramatically longer than the "after" bar.
export function toMinutes(t: string): number {
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
export function slotPositions(slots: Slot[], scaleMin: number, scaleMax: number): number[] {
  const span = scaleMax - scaleMin || 1
  return slots.map(s => {
    const v = toMinutes(s.time)
    return DOT_MARGIN + ((v - scaleMin) / span) * (100 - 2 * DOT_MARGIN)
  })
}

// ── Components ────────────────────────────────────────────────────────────────

export function TimelineBar({ track, isOld, scaleMin, scaleMax }: {
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

        {/* Filled portion */}
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

        {/* Numbered dots */}
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

      {/* Legend */}
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

export function ScenarioBlock({ title, oldTrack, newTrack, saving, savingLabel, scaleOrigin }: {
  title: string; oldTrack: Track; newTrack: Track; saving: string; savingLabel: string
  scaleOrigin?: number
}) {
  const oldTimes = oldTrack.slots.map(s => toMinutes(s.time))
  const allTimes = [...oldTimes, ...newTrack.slots.map(s => toMinutes(s.time))]
  const scaleMin = scaleOrigin ?? Math.min(...allTimes)
  const scaleMax = Math.max(...oldTimes)

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: 2, overflow: 'hidden' }}>
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
