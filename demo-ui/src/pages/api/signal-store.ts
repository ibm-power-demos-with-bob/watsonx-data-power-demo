import fs from 'fs'
import os from 'os'
import path from 'path'

export type SignalScenario = 'supplier-cyber-incident' | 'eu-wildfire'

export type SignalEvent = {
  event_id: string
  event_type?: string
  scenario: SignalScenario
  timestamp: string
  epoch_ms?: number
  signal_category: string
  signal_code: string
  affected_sector: string
  severity: string
  headline: string
  detail_url?: string
  temp_celsius?: number | null
  ticker_symbol?: string | null
  price_change_pct?: number | null
  injected?: boolean
  source_feed?: string
  source_channel?: string
  _source?: 'live' | 'stub'
}

const STORE_PATH = path.join(os.tmpdir(), 'wxd-demo-signals.json')

export function readSignalStore(): SignalEvent[] {
  try {
    const raw = fs.readFileSync(STORE_PATH, 'utf8')
    return JSON.parse(raw) as SignalEvent[]
  } catch {
    return []
  }
}

export function writeSignalStore(signals: SignalEvent[]): void {
  fs.writeFileSync(STORE_PATH, JSON.stringify(signals), 'utf8')
}

export function pushSignal(signal: SignalEvent): void {
  const store = readSignalStore()
  if (store.find((item) => item.event_id === signal.event_id)) return
  if (store.length >= 20) store.shift()
  store.push(signal)
  writeSignalStore(store)
}

export function clearSignalStore(): void {
  writeSignalStore([])
}
