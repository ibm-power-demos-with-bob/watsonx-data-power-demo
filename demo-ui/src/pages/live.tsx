/**
 * Page 2 — "The Live Satnav"
 *
 * Accepts ?scenario=cyber|wildfire to show only the relevant signal for that
 * arc of the demo. Navigation wires the full story loop:
 *
 *   / → /live?scenario=cyber → /outcome?scenario=cyber
 *     → /live?scenario=wildfire → /outcome?scenario=wildfire → /
 */

import Head from 'next/head'
import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/router'
import type { AlertCard } from './api/alerts'

const PosStreamPanel     = dynamic(() => import('../components/PosStreamPanel'),     { ssr: false })
const SignalControlPanel = dynamic(() => import('../components/SignalControlPanel'),  { ssr: false })
const AlertCardsPanel    = dynamic(() => import('../components/AlertCardsPanel'),     { ssr: false })
const DataSourcePanel    = dynamic(() => import('../components/DataSourcePanel'),     { ssr: false })

const POLL_INTERVAL_MS = 5000

const SCENARIO_META = {
  cyber: {
    label: 'Scenario 1 — Supplier Cyber Incident',
    outcomeHref: '/outcome?scenario=cyber',
    headerSub: 'Cyber Incident Arc',
    feedLabel: 'Live Cyber Threat Intelligence (Known Exploited Vulnerabilities)',
  },
  wildfire: {
    label: 'Scenario 2 — Corridor Disruption Road Closure',
    outcomeHref: '/outcome?scenario=wildfire',
    headerSub: 'Freight Corridor Arc',
    feedLabel: 'Live Route & Freight Corridor Telemetry (A9/AP-7 Corridor)',
  },
}

// Force SSR so router.query (scenario param) is available on first render
export const getServerSideProps = () => ({ props: {} })

export default function LivePage() {
  const router = useRouter()
  // router.isReady is false on the very first SSR render — wait for hydration
  // before reading query params so the scenario never flashes wrong.
  const scenario = router.isReady
    ? (router.query.scenario as string) === 'wildfire' ? 'wildfire' : 'cyber'
    : null
  const meta = scenario ? SCENARIO_META[scenario] : SCENARIO_META['cyber']

  const [alerts, setAlerts] = useState<AlertCard[]>([])
  const [loadingAlerts, setLoadingAlerts] = useState(false)

  const pollAlerts = useCallback(async () => {
    if (!scenario) return
    try {
      const res = await fetch(`/api/alerts?scenario=${scenario}`)
      if (res.ok) {
        const data = await res.json()
        setAlerts(data.alerts ?? [])
      }
    } catch { /* ignore */ }
  }, [scenario])

  // On scenario mount: clear store first, THEN start polling.
  // Sequential await prevents the race where poll repopulates before DELETE lands.
  useEffect(() => {
    if (!scenario) return
    let cancelled = false
    setAlerts([])
    setLoadingAlerts(true)
    fetch('/api/alerts', { method: 'DELETE' })
      .catch(() => {/* ignore */})
      .then(() => { if (!cancelled) return pollAlerts() })
      .finally(() => { if (!cancelled) setLoadingAlerts(false) })
    const id = setInterval(pollAlerts, POLL_INTERVAL_MS)
    return () => { cancelled = true; clearInterval(id) }
  }, [scenario, pollAlerts])

  async function handleSignalFired() {
    await pollAlerts()
  }

  const hasAlert = alerts.length > 0

  // Don't render until router is hydrated — prevents wrong scenario flash
  if (!router.isReady) return null

  return (
    <>
      <Head>
        <title>watsonx.data on IBM Power — {meta.label}</title>
      </Head>

      <div style={{
        display: 'grid',
        gridTemplateRows: '48px 1fr',
        height: '100vh',
        background: 'var(--demo-bg)',
        color: 'var(--demo-text)',
        overflow: 'hidden',
      }}>
        {/* Top bar */}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          borderBottom: '1px solid var(--demo-border)',
          background: 'var(--demo-surface)',
          gap: 16,
          flexShrink: 0,
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 24" width="42" height="17" aria-label="IBM" style={{ flexShrink: 0 }}>
            <path fill="#1192e8" d="M0 18.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm0-4.5h10v-2H0v2zm13 13.5h26v-2H13v2zm4-4.5h18v-2H17v2zm0-4.5h18v-2H17v2zm-4-4.5h26v-2H13v2zm30 13.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2zm0-4.5h10v-2H43v2z"/>
          </svg>
          <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--demo-text)' }}>watsonx.data</span>
          <span style={{ fontSize: 12, color: 'var(--demo-text-muted)', borderLeft: '1px solid var(--demo-border)', paddingLeft: 12 }}>
            on IBM Power · {meta.headerSub}
          </span>
          <div style={{ flex: 1 }} />
          {/* Live stream indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'var(--demo-surface-2)',
            border: '1px solid var(--demo-border)',
            borderRadius: 12,
            padding: '3px 10px',
            fontSize: 11,
            color: 'var(--demo-text)',
          }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--demo-green)', display: 'inline-block' }} />
            <span>📡 Ingesting: <strong>{meta.feedLabel}</strong></span>
          </div>
          {/* Progress breadcrumb */}
          <span style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginLeft: 8 }}>
            {scenario === 'cyber' ? '③ Cyber arc' : '⑤ Corridor arc'}
          </span>
          <button onClick={() => router.push('/sources')}
            style={{ background: 'transparent', border: '1px solid var(--demo-border)', color: 'var(--demo-text-muted)', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            ← Architecture
          </button>
          <button
            onClick={() => router.push(meta.outcomeHref)}
            disabled={!hasAlert}
            style={{
              background: hasAlert ? 'var(--demo-blue)' : 'var(--demo-surface)',
              border: hasAlert ? 'none' : '1px solid var(--demo-border)',
              color: hasAlert ? '#fff' : 'var(--demo-text-muted)',
              borderRadius: 2, padding: '4px 12px', fontSize: 11,
              cursor: hasAlert ? 'pointer' : 'not-allowed', fontWeight: 600,
              transition: 'all 0.2s ease',
            }}
          >
            {hasAlert ? 'See the outcome →' : 'Inject a signal first'}
          </button>
          <span style={{ fontSize: 11, color: hasAlert ? 'var(--demo-red)' : 'var(--demo-green)', fontWeight: 700, marginLeft: 4 }}>
            {hasAlert ? `⚡ ${alerts.length} ALERT${alerts.length !== 1 ? 'S' : ''}` : '● NOMINAL'}
          </span>
        </header>

        {/* Four-panel grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 360px',
          gridTemplateRows: '1fr 1fr',
          gap: '1px',
          background: 'var(--demo-border)',
          overflow: 'hidden',
        }}>
          <div style={{ background: 'var(--demo-bg)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <PosStreamPanel />
          </div>
          <div style={{ background: 'var(--demo-bg)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {/* Only show the signal button for this arc's scenario */}
            <SignalControlPanel
              onSignalFired={handleSignalFired}
              onlyScenario={scenario === 'cyber' ? 'supplier-cyber-incident' : 'eu-wildfire'}
            />
          </div>
          <div style={{ background: 'var(--demo-bg)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <AlertCardsPanel alerts={alerts} loading={loadingAlerts} />
          </div>
          <div style={{ background: 'var(--demo-bg)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <DataSourcePanel />
          </div>
        </div>
      </div>
    </>
  )
}
