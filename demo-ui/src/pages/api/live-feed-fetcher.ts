/**
 * live-feed-fetcher.ts
 *
 * Ingests genuine live external intelligence:
 * 1. Live CISA / MITRE Known Exploited Vulnerabilities (KEV) Catalog (real active cyber threats)
 * 2. Live Corridor Weather / Atmospheric Telemetry along the A9/AP-7 European freight corridor
 *
 * This provides genuine background signals that stream through the detector continuously.
 * Real events are evaluated against business assets (and found to be non-matching/benign),
 * while synthetic injected events trigger immediate federated impact alerts.
 */

import https from 'https'
import { pushSignal, type SignalEvent } from './signal-store'

let isFetching = false
let lastFetchTime = 0
const FETCH_COOLDOWN_MS = 60000 // Ingest fresh upstream data at most once per minute

function fetchJson<T>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        headers: {
          'User-Agent': 'watsonx-data-power-demo/1.0 (IBM Presales Demo Live Feed Ingest)',
          Accept: 'application/json',
        },
        timeout: 5000,
      },
      (res) => {
        if (res.statusCode && res.statusCode >= 400) {
          reject(new Error(`HTTP ${res.statusCode}`))
          return
        }
        let data = ''
        res.on('data', (chunk) => (data += chunk))
        res.on('end', () => {
          try {
            resolve(JSON.parse(data) as T)
          } catch (e) {
            reject(e)
          }
        })
      }
    )
    req.on('error', reject)
    req.on('timeout', () => {
      req.destroy()
      reject(new Error('Timeout'))
    })
  })
}

interface CisaKevItem {
  cveID: string
  vendorProject: string
  product: string
  vulnerabilityName: string
  dateAdded: string
  shortDescription: string
}

interface CisaKevResponse {
  vulnerabilities?: CisaKevItem[]
}

interface OpenMeteoResponse {
  current?: {
    time: string
    temperature_2m: number
    wind_speed_10m: number
  }
}

export async function ingestLiveFeeds(): Promise<{ ingestedCyber: number; ingestedLogistics: number }> {
  const now = Date.now()
  if (isFetching || now - lastFetchTime < FETCH_COOLDOWN_MS) {
    return { ingestedCyber: 0, ingestedLogistics: 0 }
  }

  isFetching = true
  lastFetchTime = now
  let cyberCount = 0
  let logCount = 0

  // 1. Fetch Real Live CVEs from CISA Known Exploited Vulnerabilities Feed
  try {
    const kevData = await fetchJson<CisaKevResponse>(
      'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
    )
    if (kevData.vulnerabilities && kevData.vulnerabilities.length > 0) {
      // Pick top 3 recent vulnerabilities as background live telemetry
      const recent = kevData.vulnerabilities.slice(0, 3)
      for (const item of recent) {
        const signal: SignalEvent = {
          event_id: `live-kev-${item.cveID}`,
          event_type: 'external_signal',
          scenario: 'supplier-cyber-incident', // Evaluated in cyber detector
          timestamp: new Date().toISOString(),
          epoch_ms: Date.now(),
          signal_category: 'CYBER_INCIDENT',
          signal_code: item.cveID,
          affected_sector: 'TECHNOLOGY',
          severity: 'HIGH',
          headline: `Live Advisory: ${item.vendorProject} ${item.product} - ${item.vulnerabilityName}`,
          detail_url: `https://nvd.nist.gov/vuln/detail/${item.cveID}`,
          source_feed: 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)',
          source_channel: 'Global Cyber Threat Intelligence · Known Exploited Vulnerabilities Feed',
          injected: false,
          _source: 'live',
        }
        pushSignal(signal)
        cyberCount++
      }
    }
  } catch (err) {
    // Non-fatal if offline
  }

  // 2. Fetch Real Live Freight Corridor Conditions (A9 / Southern France Route: Lat 43.6, Lon 3.8)
  try {
    const weatherData = await fetchJson<OpenMeteoResponse>(
      'https://api.open-meteo.com/v1/forecast?latitude=43.6&longitude=3.8&current=temperature_2m,wind_speed_10m'
    )
    if (weatherData.current) {
      const temp = weatherData.current.temperature_2m
      const wind = weatherData.current.wind_speed_10m
      const signal: SignalEvent = {
        event_id: `live-route-a9-corridor`,
        event_type: 'external_signal',
        scenario: 'eu-wildfire', // Evaluated in logistics detector
        timestamp: new Date().toISOString(),
        epoch_ms: Date.now(),
        signal_category: 'LOGISTICS_DISRUPTION',
        signal_code: 'A9_AP7_CORRIDOR_TELEMETRY',
        affected_sector: 'LOGISTICS',
        severity: temp > 40 ? 'CRITICAL' : 'LOW',
        headline: `A9 Freight Corridor Live Telemetry: ${temp}°C, Wind ${wind} km/h · Transit nominal`,
        detail_url: 'https://api.open-meteo.com',
        temp_celsius: temp,
        source_feed: 'Route & Environmental Intelligence',
        source_channel: 'Corridor Sensor Telemetry (A9 Lyon–Barcelona)',
        injected: false,
        _source: 'live',
      }
      pushSignal(signal)
      logCount++
    }
  } catch (err) {
    // Non-fatal if offline
  }

  isFetching = false
  return { ingestedCyber: cyberCount, ingestedLogistics: logCount }
}
