/**
 * PosStreamPanel
 *
 * Connects to /api/pos-stream (SSE) and renders a scrolling list of
 * recent POS transactions.  The panel label "Source 3 — Iceberg / COS"
 * is the architecture talking point: this stream will eventually feed
 * the real Iceberg table; until then the same component works with the
 * synthetic SSE stream.
 */

'use client'

import { useEffect, useRef, useState } from 'react'
import { Tag } from '@carbon/react'

type PosEvent = {
  event_id: string
  timestamp: string
  transaction_id: string
  store_id: string
  region: string
  sku_id: string
  sector: string
  quantity: number
  unit_price: number
  total_amount: number
  payment_method: string
  inventory_remaining_estimate: number
}

const MAX_EVENTS = 60

type TagColor = 'blue' | 'cyan' | 'gray' | 'green' | 'magenta' | 'purple' | 'red' | 'teal' | 'cool-gray' | 'warm-gray'

const SECTOR_COLORS: Record<string, TagColor> = {
  TECHNOLOGY:       'blue',
  FOOD_BEVERAGE:    'green',
  FASHION:          'purple',
  HOME_GOODS:       'teal',
  CONSUMER_LEISURE: 'cyan',
  AUTOMOTIVE:       'warm-gray',
  LOGISTICS:        'cool-gray',
  HEALTH_BEAUTY:    'magenta',
}

function fmt(n: number) {
  return `£${n.toFixed(2)}`
}

function tsShort(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso.slice(11, 19)
  }
}

export default function PosStreamPanel() {
  const [events, setEvents] = useState<PosEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [count, setCount] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const es = new EventSource('/api/pos-stream')

    es.onopen = () => setConnected(true)

    es.onmessage = (e) => {
      try {
        const evt: PosEvent = JSON.parse(e.data)
        setEvents((prev) => {
          const next = [evt, ...prev]
          return next.slice(0, MAX_EVENTS)
        })
        setCount((c) => c + 1)
      } catch {
        // ignore bad frames
      }
    }

    es.onerror = () => setConnected(false)

    return () => es.close()
  }, [])

  // Auto-scroll to top (newest events arrive at top)
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [events.length])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Panel header */}
      <div
        style={{
          padding: '12px 16px 10px',
          borderBottom: '1px solid var(--demo-border)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          flexShrink: 0,
        }}
      >
        <span className="live-dot" />
        <span style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.02em', flex: 1 }}>
          LIVE POS STREAM
        </span>
        <span
          style={{
            fontSize: 11,
            color: connected ? 'var(--demo-green)' : 'var(--demo-text-muted)',
            fontFamily: 'IBM Plex Mono, monospace',
          }}
        >
          {connected ? `● ${count} txn` : '○ connecting…'}
        </span>
      </div>

      {/* Source label */}
      <div
        style={{
          padding: '6px 16px',
          borderBottom: '1px solid var(--demo-border)',
          display: 'flex',
          gap: 6,
          flexShrink: 0,
          background: 'var(--demo-surface)',
        }}
      >
        <span className="source-badge badge-iceberg">⬡ Iceberg / COS</span>
        <span
          style={{
            fontSize: 11,
            color: 'var(--demo-text-muted)',
            alignSelf: 'center',
            marginLeft: 4,
          }}
        >
          Source 3 · retail_pos_events
        </span>
      </div>

      {/* Signpost — why this stream matters to the story */}
      <div
        style={{
          padding: '6px 16px',
          borderBottom: '1px solid var(--demo-border)',
          fontSize: 11,
          color: 'var(--demo-text-muted)',
          lineHeight: 1.5,
          background: '#1a1a1a',
          flexShrink: 0,
          borderLeft: '3px solid var(--demo-teal)',
        }}
      >
        This is your business <strong style={{ color: 'var(--demo-text)' }}>right now</strong> —
        not Friday's report. Sector tags show which product lines are exposed the moment a signal fires.
      </div>

      {/* Event list */}
      <div
        ref={scrollRef}
        className="pos-stream-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '4px 0',
        }}
      >
        {events.length === 0 && (
          <div
            style={{
              padding: '24px 16px',
              color: 'var(--demo-text-muted)',
              fontSize: 12,
              textAlign: 'center',
            }}
          >
            Waiting for events…
          </div>
        )}
        {events.map((evt) => (
          <div
            key={evt.event_id}
            style={{
              padding: '7px 16px',
              borderBottom: '1px solid #2d2d2d',
              display: 'grid',
              gridTemplateColumns: '56px 1fr auto',
              alignItems: 'center',
              gap: '8px',
              fontSize: 12,
              fontFamily: 'IBM Plex Mono, monospace',
            }}
          >
            {/* Time */}
            <span style={{ color: 'var(--demo-text-muted)', fontSize: 11 }}>
              {tsShort(evt.timestamp)}
            </span>

            {/* Store + SKU */}
            <div>
              <div style={{ fontWeight: 500, color: 'var(--demo-text)', marginBottom: 1 }}>
                {evt.store_id}
              </div>
              <div style={{ color: 'var(--demo-text-muted)', fontSize: 11 }}>
                {evt.sku_id} · {evt.payment_method}
              </div>
            </div>

            {/* Amount + sector tag */}
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 600, color: 'var(--demo-teal)' }}>
                {fmt(evt.total_amount)}
              </div>
              <Tag
                type={SECTOR_COLORS[evt.sector] ?? 'gray'}
                size="sm"
                style={{ marginTop: 2, fontSize: 9 }}
              >
                {evt.sector}
              </Tag>
            </div>
          </div>
        ))}
      </div>

      {/* Footer: inventory alert indicators */}
      <div
        style={{
          padding: '8px 16px',
          borderTop: '1px solid var(--demo-border)',
          display: 'flex',
          gap: 16,
          flexShrink: 0,
          background: 'var(--demo-surface)',
          fontSize: 11,
          color: 'var(--demo-text-muted)',
        }}
      >
        <span>
          Low stock (≤10):{' '}
          <span style={{ color: 'var(--demo-orange)', fontWeight: 600 }}>
            {events.filter((e) => e.inventory_remaining_estimate <= 10).length}
          </span>
        </span>
        <span>
          Critical (≤3):{' '}
          <span style={{ color: 'var(--demo-red)', fontWeight: 600 }}>
            {events.filter((e) => e.inventory_remaining_estimate <= 3).length}
          </span>
        </span>
      </div>
    </div>
  )
}
