/**
 * SignalControlPanel
 *
 * The "Fire Signal" panel.  Two primary buttons — supplier-cyber-incident
 * and eu-wildfire — matching the two-arc demo narrative from
 * checkpoint-architecture.md.
 *
 * Calls POST /api/inject-signal to place a synthetic incident into the signal
 * store, then POST /api/alerts to run the separate business-relevance detector.
 */

'use client'

import { useState } from 'react'
import { Button, InlineLoading, InlineNotification } from '@carbon/react'
import { Warning, EventSchedule, Flood } from '@carbon/icons-react'

type SignalScenario = 'supplier-cyber-incident' | 'eu-wildfire'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type OnSignalFired = (scenario: SignalScenario) => void

interface Props {
  onSignalFired?: OnSignalFired
  disabled?: boolean
  /** When set, only this scenario's button is shown */
  onlyScenario?: SignalScenario
}

const SCENARIO_META: Record<
  SignalScenario,
  {
    label: string
    sublabel: string
    category: string
    upstreamFeed: string
    colour: string
    icon: React.ElementType
    presenterCue: string
  }
> = {
  'supplier-cyber-incident': {
    label: 'Supplier Cyber Incident',
    sublabel: 'Threat Intelligence Feed · Known Exploited Vulnerabilities',
    category: 'CYBER_INCIDENT',
    upstreamFeed: 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)',
    colour: 'var(--demo-red)',
    icon: EventSchedule,
    presenterCue:
      '"Live Cyber Threat Intelligence feed flagged the zero-day vulnerability. Your ERP never heard of the tier-2 supplier, but watsonx.data joined the feed with EDB & IBM i to reveal £47k exposure in seconds."',
  },
  'eu-wildfire': {
    label: 'Corridor Disruption — Road Closure',
    sublabel: 'Route Intelligence Feed · Freight at Risk',
    category: 'LOGISTICS_DISRUPTION',
    upstreamFeed: 'Route & Travel Intelligence',
    colour: 'var(--demo-orange)',
    icon: Flood,
    presenterCue:
      '"Live route disruption intelligence flagged the A9/AP-7 closure this morning. Your weekly freight report was printed last Friday. watsonx.data joined the disruption feed to pinpoint 3 at-risk POs."',
  },
}

function ScenarioButton({
  scenario,
  onFired,
  globalFiring,
  onFiringStart,
}: {
  scenario: SignalScenario
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onFired: () => void
  globalFiring: boolean
  onFiringStart: () => void
}) {
  const [firing, setFiring] = useState(false)
  const [fired, setFired] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const meta = SCENARIO_META[scenario]
  const Icon = meta.icon

  async function fire() {
    setFiring(true)
    onFiringStart()
    setError(null)
    try {
      const res = await fetch('/api/inject-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const detectRes = await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!detectRes.ok) throw new Error(`HTTP ${detectRes.status}`)
      setFired(true)
      onFired()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setFiring(false)
    }
  }

  return (
    <div
      style={{
        background: 'var(--demo-surface)',
        border: `1px solid ${fired ? meta.colour : 'var(--demo-border)'}`,
        borderRadius: 2,
        padding: '16px',
        transition: 'border-color 0.3s ease',
      }}
    >
      {/* Scenario header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <Icon size={20} style={{ color: meta.colour, flexShrink: 0, marginTop: 1 }} />
        <div>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--demo-text)' }}>
            {meta.label}
          </div>
          <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginTop: 2 }}>
            {meta.sublabel}
          </div>
        </div>
        <div style={{ marginLeft: 'auto', flexShrink: 0 }}>
          <span
            className="source-badge"
            style={{
              background: 'transparent',
              border: `1px solid ${meta.colour}`,
              color: meta.colour,
            }}
          >
            {meta.category}
          </span>
        </div>
      </div>

      {/* Presenter cue (collapsed until fired) */}
      {fired && (
        <div
          style={{
            background: '#1a1a1a',
            border: `1px solid ${meta.colour}33`,
            borderLeft: `3px solid ${meta.colour}`,
            borderRadius: 2,
            padding: '8px 12px',
            marginBottom: 10,
            fontSize: 12,
            color: 'var(--demo-text-muted)',
            fontStyle: 'italic',
            lineHeight: 1.5,
          }}
        >
          💬 {meta.presenterCue}
        </div>
      )}

      {error && (
        <InlineNotification
          kind="error"
          title="Injection failed: "
          subtitle={error}
          style={{ marginBottom: 8 }}
          lowContrast
        />
      )}

      {/* Fire button */}
      {firing ? (
        <InlineLoading description="Injecting signal…" status="active" />
      ) : (
        <Button
          kind={fired ? 'ghost' : 'danger'}
          size="sm"
          disabled={globalFiring && !firing}
          onClick={fire}
          renderIcon={Warning}
          style={{ width: '100%' }}
        >
          {fired ? '⚡ Inject Again' : '⚡ Inject Signal'}
        </Button>
      )}
    </div>
  )
}

export default function SignalControlPanel({ onSignalFired, disabled, onlyScenario }: Props) {
  const [firingAny, setFiringAny] = useState(false)

  const scenarios: SignalScenario[] = onlyScenario
    ? [onlyScenario]
    : ['supplier-cyber-incident', 'eu-wildfire']

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
        <span style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.02em' }}>
          MONITORED SIGNAL INJECTION
        </span>
        <span style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginLeft: 'auto' }}>
          External Intelligence Feeds
        </span>
      </div>

      {/* Description */}
      <div
        style={{
          padding: '10px 16px',
          borderBottom: '1px solid var(--demo-border)',
          fontSize: 12,
          color: 'var(--demo-text-muted)',
          lineHeight: 1.5,
          background: 'var(--demo-surface)',
          flexShrink: 0,
        }}
      >
        {onlyScenario === 'eu-wildfire' ? (
          <>Simulate a road closure event arriving on the monitored <strong>Route &amp; Travel Disruption</strong> channel. The detector checks warehouse routes in EDB and active purchase orders in IBM i to pinpoint exposed freight.</>
        ) : (
          <>Simulate a zero-day vulnerability alert arriving on the monitored <strong>Cybersecurity Threat Intelligence</strong> channel. The detector checks tier-2 suppliers in EDB and active purchase orders in IBM i to calculate exposure.</>
        )}
      </div>

      {/* Scenario buttons */}
      <div
        style={{
          flex: 1,
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          opacity: disabled ? 0.5 : 1,
          pointerEvents: disabled ? 'none' : undefined,
        }}
      >
        {scenarios.map((s) => (
          <ScenarioButton
            key={s}
            scenario={s}
            globalFiring={firingAny}
            onFiringStart={() => setFiringAny(true)}
            onFired={() => {
              setFiringAny(false)
              onSignalFired?.(s)
            }}
          />
        ))}
      </div>

      {/* Footer note */}
      <div
        style={{
          padding: '8px 16px',
          borderTop: '1px solid var(--demo-border)',
          fontSize: 11,
          color: 'var(--demo-text-muted)',
          flexShrink: 0,
          background: 'var(--demo-surface)',
        }}
      >
        Scenarios reference real documented events — no political dimension.
        <br />
        <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
          signal-injector.py supplier-cyber-incident
        </span>
      </div>
    </div>
  )
}
