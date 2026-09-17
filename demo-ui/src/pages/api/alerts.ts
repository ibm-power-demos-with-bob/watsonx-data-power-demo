/**
 * GET  /api/alerts?scenario=cyber|wildfire  — returns filtered alerts
 * DELETE /api/alerts                         — clears all alerts (new scenario arc)
 *
 * Alerts are stored in a temp JSON file so all Next.js worker processes share
 * the same state.  In-memory module-level arrays are NOT shared across workers
 * in production (npm start), which caused stale alerts to persist after DELETE.
 */

import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'
import os from 'os'
import { runDetection } from './detect-signals'
import { clearSignalStore } from './signal-store'

export type AlertCard = {
  id: string
  scenario: 'supplier-cyber-incident' | 'eu-wildfire'
  firedAt: string
  signal: {
    signal_category: string
    signal_code: string
    severity: string
    headline: string
    affected_sector: string
    detail_url?: string
    temp_celsius?: number | null
    source_feed?: string
    source_channel?: string
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  alert: Record<string, any> | null
  source: 'live' | 'stub'
}

const STORE_PATH = path.join(os.tmpdir(), 'wxd-demo-alerts.json')

export function readStore(): AlertCard[] {
  try {
    const raw = fs.readFileSync(STORE_PATH, 'utf8')
    return JSON.parse(raw) as AlertCard[]
  } catch {
    return []
  }
}

export function writeStore(alerts: AlertCard[]): void {
  fs.writeFileSync(STORE_PATH, JSON.stringify(alerts), 'utf8')
}

export function pushAlert(card: AlertCard): void {
  const store = readStore()
  // Deduplicate by id
  if (store.find(a => a.id === card.id)) return
  if (store.length >= 10) store.shift()
  store.push(card)
  writeStore(store)
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'DELETE') {
    writeStore([])
    clearSignalStore()
    res.status(200).json({ cleared: true })
    return
  }

  if (req.method === 'POST') {
    const detections = await runDetection()
    res.status(200).json({ detections })
    return
  }

  const store = readStore()
  const { scenario } = req.query
  const filtered = scenario
    ? store.filter(a =>
        scenario === 'cyber'
          ? a.scenario === 'supplier-cyber-incident'
          : a.scenario === 'eu-wildfire'
      )
    : store

  res.status(200).json({ alerts: filtered })
}
