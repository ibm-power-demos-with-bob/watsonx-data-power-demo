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
import { HeaderName } from '@carbon/react'
import type { AlertCard } from './api/alerts'
// No carbon icons needed - using text alternatives
import { useAudience } from '../context/AudienceContext'

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
  const { isSecurity, isTechnical, isExecutive, isOperations } = useAudience()
  // router.isReady is false on the very first SSR render — wait for hydration
  // before reading query params so the scenario never flashes wrong.
  const scenario = router.isReady
    ? (router.query.scenario as string) === 'wildfire' ? 'wildfire' : 'cyber'
    : null
  const meta = scenario ? SCENARIO_META[scenario] : SCENARIO_META['cyber']

  const [alerts, setAlerts] = useState<AlertCard[]>([])
  const [loadingAlerts, setLoadingAlerts] = useState(false)
  const [showHowItWorks, setShowHowItWorks] = useState(false)
  const [queryExecuting, setQueryExecuting] = useState(false)
  const [queryScenario, setQueryScenario] = useState<'supplier-cyber-incident' | 'eu-wildfire' | null>(null)

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
    // Start query execution indicator
    const signalScenario = scenario === 'cyber' ? 'supplier-cyber-incident' : 'eu-wildfire'
    setQueryExecuting(true)
    setQueryScenario(signalScenario)
    
    await pollAlerts()
    
    // Clear query execution indicator when alert appears
    if (alerts.length > 0) {
      setQueryExecuting(false)
      setQueryScenario(null)
    }
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
          <HeaderName prefix="IBM" href="/" style={{ paddingLeft: 0, textDecoration: 'none' }}>
            watsonx.data
          </HeaderName>
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
          {/* Production Pipeline Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'var(--demo-surface-2)',
            border: '1px solid var(--demo-border)',
            borderRadius: 12,
            padding: '3px 10px',
            fontSize: 10,
            color: 'var(--demo-text-muted)',
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--demo-orange)', display: 'inline-block' }} />
            <span>🏭 Production: Continuous Pipeline</span>
            <span style={{ color: 'var(--demo-text-muted)', cursor: 'help', fontSize: 12 }} title="In production: CISA KEV polling (5-min), route webhooks, Kafka/Flink stream processor auto-triggers federation → SIEM/SOAR">ℹ</span>
          </div>
          {/* Progress breadcrumb */}
          <span style={{ fontSize: 11, color: 'var(--demo-text-muted)', marginLeft: 8 }}>
            {scenario === 'cyber' ? '③ Cyber arc' : '⑤ Corridor arc'}
          </span>
          <button onClick={() => router.push('/sources')}
            style={{ background: 'transparent', border: '1px solid var(--demo-border)', color: 'var(--demo-text-muted)', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            ← Architecture
          </button>
          {/* Audience indicator badge */}
          {(isSecurity || isTechnical || isOperations || isExecutive) && (
            <span style={{
              background: 'var(--demo-surface-2)',
              border: '1px solid var(--demo-border)',
              borderRadius: 12,
              padding: '3px 10px',
              fontSize: 10,
              fontWeight: 600,
              color: isSecurity ? 'var(--demo-red)' : isTechnical ? 'var(--demo-purple)' : isOperations ? 'var(--demo-green)' : 'var(--demo-blue)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}>
              {isSecurity && '🔒 SEC'}
              {isTechnical && '🔧 TECH'}
              {isOperations && '📦 OPS'}
              {isExecutive && '🎯 EXEC'}
            </span>
          )}
          {/* How Detection Works Link — show for technical/security audiences */}
          {(isTechnical || isSecurity) && (
            <button
              onClick={() => setShowHowItWorks(true)}
              style={{
                background: 'transparent',
                border: '1px solid var(--demo-border)',
                color: 'var(--demo-text-muted)',
                borderRadius: 2,
                padding: '4px 12px',
                fontSize: 11,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
              title="How does detection work? (Demo vs Production)"
            >
              <span style={{ fontSize: 12 }}>ℹ</span>
              <span>How it works</span>
            </button>
          )}
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
            <AlertCardsPanel
              alerts={alerts}
              loading={loadingAlerts}
              queryExecuting={queryExecuting}
              scenario={queryScenario ?? undefined}
              isSecurity={isSecurity}
              isTechnical={isTechnical}
              isExecutive={isExecutive}
              isOperations={isOperations}
            />
          </div>
          <div style={{ background: 'var(--demo-bg)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <DataSourcePanel
              scenario={queryScenario ?? undefined}
              queryExecuting={queryExecuting}
              isSecurity={isSecurity}
              isTechnical={isTechnical}
              isExecutive={isExecutive}
              isOperations={isOperations}
            />
          </div>
        </div>
      </div>

      {/* How Detection Works Modal */}
      {showHowItWorks && (
        <div
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
          onClick={() => setShowHowItWorks(false)}
        >
          <div
            style={{
              background: 'var(--demo-surface)',
              border: '1px solid var(--demo-border)',
              borderRadius: 4,
              padding: '24px',
              maxWidth: 800,
              maxHeight: '90vh',
              overflow: 'auto',
              color: 'var(--demo-text)',
              fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 20,
              paddingBottom: 16,
              borderBottom: '1px solid var(--demo-border)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 20, color: 'var(--demo-blue)' }}>ℹ</span>
                <span style={{ fontWeight: 700, fontSize: 16 }}>How Detection Works — Demo vs Production</span>
              </div>
              <button
                onClick={() => setShowHowItWorks(false)}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--demo-border)',
                  color: 'var(--demo-text-muted)',
                  borderRadius: 2,
                  padding: '6px 12px',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>

            {/* Satnav Analogy */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 12, color: 'var(--demo-blue)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 12 }}>
                Think of It Like Your Satnav
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
                <div style={{ background: 'var(--demo-bg)', border: '1px solid var(--demo-border)', borderRadius: 4, padding: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>📡</div>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>1. Traffic Report Arrives</div>
                  <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>CISA KEV feed / Route telemetry / Weather API signals an event</div>
                </div>
                <div style={{ background: 'var(--demo-bg)', border: '1px solid var(--demo-border)', borderRadius: 4, padding: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>🧭</div>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>2. Satnav Checks Your Route</div>
                  <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>Federated query joins signal → your supplier graph & delivery lanes</div>
                </div>
                <div style={{ background: 'var(--demo-bg)', border: '1px solid var(--demo-border)', borderRadius: 4, padding: '16px', textAlign: 'center' }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>⚡</div>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>3. Reroute Alert</div>
                  <div style={{ fontSize: 11, color: 'var(--demo-text-muted)' }}>Quantified exposure surfaced → Action taken</div>
                </div>
              </div>
            </div>

            {/* Demo vs Production Comparison */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 12, color: 'var(--demo-blue)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 12 }}>
                Demo Mode vs Production Mode
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
                <thead>
                  <tr style={{ background: 'var(--demo-bg)', borderBottom: '1px solid var(--demo-border)' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--demo-text)', borderRight: '1px solid var(--demo-border)' }}>Step</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--demo-text)', borderRight: '1px solid var(--demo-border)' }}>Demo (This Page)</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: 'var(--demo-text)' }}>Production</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid var(--demo-border)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text-muted)', borderRight: '1px solid var(--demo-border)' }}>Signal Source</td>
                    <td style={{ padding: '8px 12px', borderRight: '1px solid var(--demo-border)' }}>
                      <code>signal-injector.py</code> (Python script)
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      CISA KEV API (polling 5-min) · Route telemetry webhooks · Weather APIs
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--demo-border)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text-muted)', borderRight: '1px solid var(--demo-border)' }}>Ingestion</td>
                    <td style={{ padding: '8px 12px', borderRight: '1px solid var(--demo-border)' }}>
                      JSON file in <code>/tmp/wxd-demo-signals.json</code>
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      Kafka / Event Streams topic → normalised & enriched
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--demo-border)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text-muted)', borderRight: '1px solid var(--demo-border)' }}>Trigger</td>
                    <td style={{ padding: '8px 12px', borderRight: '1px solid var(--demo-border)' }}>
                      Presenter clicks "Inject Signal" → <code>POST /api/alerts</code>
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      Flink / Kafka Streams processor auto-triggers on new signal
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--demo-border)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text-muted)', borderRight: '1px solid var(--demo-border)' }}>Federation</td>
                    <td style={{ padding: '8px 12px', borderRight: '1px solid var(--demo-border)' }}>
                      Presto SQL: IBM i × PostgreSQL × Iceberg (under 2s)
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      Same Presto SQL, auto-executed on signal match
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text-muted)', borderRight: '1px solid var(--demo-border)' }}>Alert Output</td>
                    <td style={{ padding: '8px 12px', borderRight: '1px solid var(--demo-border)' }}>
                      Browser alert card (<code>source: "live"</code>)
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      SIEM (QRadar/Splunk) · SOAR · ServiceNow · PagerDuty · Auto-remediation
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Technical Footnote */}
            <div style={{
              background: 'var(--demo-bg)',
              border: '1px solid var(--demo-border)',
              borderRadius: 4,
              padding: '16px',
              fontSize: 11,
              color: 'var(--demo-text-muted)',
              lineHeight: 1.6,
            }}>
              <strong style={{ color: 'var(--demo-text)' }}>Technical note for architects:</strong> The federation layer is identical — zero-ETL Presto query across IBM i (Db2 for i), PostgreSQL/EDB, and Apache Iceberg on Cloud Object Storage, executing in under 2 seconds on RHEL on IBM Power. The demo simplifies the trigger (button vs continuous pipeline) and alert sink (browser vs SIEM/SOAR) for narrative clarity. In production, watsonx.data on IBM Power runs the same query; the ingestion pipeline (Kafka/Flink on OpenShift) and response automation (ServiceNow/Ansible) are the operational additions.
            </div>
          </div>
        </div>
      )}

    </>
  )
}
