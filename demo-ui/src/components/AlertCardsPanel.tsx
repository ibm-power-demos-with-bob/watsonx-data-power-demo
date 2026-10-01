/**
 * AlertCardsPanel
 *
 * Renders the federated query result alert cards.
 * Card implementations → CyberAlertCard.tsx, WildfireAlertCard.tsx
 */

'use client'

import { useEffect, useState } from 'react'
import { Button, SkeletonText } from '@carbon/react'
import { Warning } from '@carbon/icons-react'
import type { AlertCard } from '../pages/api/alerts'
import { CyberAlertCard } from './CyberAlertCard'
import { WildfireAlertCard } from './WildfireAlertCard'

interface Props {
  alerts: AlertCard[]
  loading?: boolean
  queryExecuting?: boolean
  scenario?: 'supplier-cyber-incident' | 'eu-wildfire'
  isSecurity?: boolean
  isTechnical?: boolean
  isExecutive?: boolean
  isOperations?: boolean
}

export default function AlertCardsPanel({ alerts, loading, queryExecuting, scenario, isSecurity, isTechnical, isExecutive, isOperations }: Props) {
  const [localAlerts, setLocalAlerts] = useState<AlertCard[]>([])

  useEffect(() => {
    setLocalAlerts(alerts)
  }, [alerts])

  const displayed = localAlerts.length > 0 ? localAlerts : []

  const queryStatusText = queryExecuting
    ? scenario === 'supplier-cyber-incident'
      ? 'Running federated query: IBM i (orders) × EDB (tier2_suppliers) × Iceberg (CISA KEV)...'
      : 'Running federated query: IBM i (orders) × EDB (warehouse_routes) × Iceberg (Route Telemetry)...'
    : ''

  const audienceBadge = isSecurity ? (
    <span style={{ background: '#da1e2822', border: '1px solid #da1e28', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#da1e28', textTransform: 'uppercase' }}>🔒 SEC VIEW</span>
  ) : isTechnical ? (
    <span style={{ background: '#a855f722', border: '1px solid #a855f7', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#a855f7', textTransform: 'uppercase' }}>🔧 TECH VIEW</span>
  ) : isOperations ? (
    <span style={{ background: '#24a14822', border: '1px solid #24a148', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#24a148', textTransform: 'uppercase' }}>📦 OPS VIEW</span>
  ) : isExecutive ? (
    <span style={{ background: '#0f62fe22', border: '1px solid #0f62fe', borderRadius: 2, padding: '2px 8px', fontSize: 9, fontWeight: 600, color: '#0f62fe', textTransform: 'uppercase' }}>🎯 EXEC VIEW</span>
  ) : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px 10px',
        borderBottom: '1px solid var(--demo-border)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        flexShrink: 0,
      }}>
        <Warning size={16} style={{ color: 'var(--demo-red)' }} />
        <span style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.02em', flex: 1 }}>
          SIDECAR ALERTS
        </span>
        {audienceBadge}
        {displayed.length > 0 && (
          <span style={{
            background: 'var(--demo-red)',
            color: '#fff',
            borderRadius: 8,
            fontSize: 10,
            fontWeight: 700,
            padding: '1px 7px',
            minWidth: 20,
            textAlign: 'center',
          }}>
            {displayed.length}
          </span>
        )}
      </div>

      {/* Query Execution Indicator */}
      {queryExecuting && (
        <div style={{
          padding: '10px 16px',
          borderBottom: '1px solid var(--demo-border)',
          background: '#1a1a2e',
          borderLeft: '4px solid var(--demo-blue)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{
            width: 16, height: 16, borderRadius: '50%',
            border: '2px solid var(--demo-blue)',
            borderTopColor: 'transparent',
            animation: 'spin 1s linear infinite',
          }} />
          <span style={{ fontSize: 11, color: 'var(--demo-blue)', fontWeight: 600, fontFamily: 'IBM Plex Mono, monospace' }}>
            {queryStatusText}
          </span>
        </div>
      )}

      {/* Source label */}
      <div style={{
        padding: '6px 16px',
        borderBottom: '1px solid var(--demo-border)',
        display: 'flex',
        gap: 6,
        flexShrink: 0,
        background: 'var(--demo-surface)',
      }}>
        <span className="source-badge badge-ibmi">IBM i</span>
        <span className="source-badge badge-edb">EDB Postgres</span>
        <span className="source-badge badge-iceberg">Iceberg</span>
        <span style={{ fontSize: 11, color: 'var(--demo-text-muted)', alignSelf: 'center', marginLeft: 4 }}>
          Federated · 3-source join
        </span>
        {queryExecuting && (
          <span style={{ fontSize: 10, color: 'var(--demo-blue)', fontWeight: 600, marginLeft: 'auto', fontFamily: 'IBM Plex Mono, monospace' }}>
            {'<2s'}
          </span>
        )}
      </div>

      {/* Card list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {loading && displayed.length === 0 && (
          <SkeletonText paragraph lineCount={6} />
        )}

        {!loading && displayed.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '32px 16px',
            color: 'var(--demo-text-muted)',
            fontSize: 12,
            lineHeight: 1.7,
          }}>
            <Warning size={24} style={{ color: 'var(--demo-border)', marginBottom: 12 }} />
            <br />
            No alerts yet.
            <br />
            Use the Signal Injection panel to inject a scenario.
          </div>
        )}

        {displayed.slice().reverse().map((card) =>
          card.scenario === 'supplier-cyber-incident' ? (
            <CyberAlertCard
              key={card.id}
              card={card}
              isSecurity={isSecurity}
              isTechnical={isTechnical}
              isExecutive={isExecutive}
              isOperations={isOperations}
            />
          ) : (
            <WildfireAlertCard
              key={card.id}
              card={card}
              isSecurity={isSecurity}
              isTechnical={isTechnical}
              isExecutive={isExecutive}
              isOperations={isOperations}
            />
          )
        )}

        {displayed.length > 0 && (
          <Button
            kind="ghost"
            size="sm"
            onClick={() => setLocalAlerts([])}
            style={{ width: '100%', color: 'var(--demo-text-muted)', marginTop: 4 }}
          >
            Clear alerts
          </Button>
        )}
      </div>
    </div>
  )
}
