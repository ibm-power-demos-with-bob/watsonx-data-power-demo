/**
 * POST /api/inject-signal
 *
 * Body: { scenario: "supplier-cyber-incident" | "eu-wildfire" }
 *
 * Executes event-generators/signal-injector.py on the server (via Python
 * subprocess) and returns the emitted JSON signal event.
 *
 * When the Iceberg writer is wired the signal-injector.py output is written
 * into the Iceberg table.  Until that is in place the JSON is returned
 * directly to the UI, which uses it to drive the simulated alert cards.
 *
 * For the demo VM: signal-injector.py is at
 *   /home/ec2-user/watsonx-data-power-demo/event-generators/signal-injector.py
 * The Next.js process must be started from the repo root so that relative
 * paths resolve correctly.
 */

import type { NextApiRequest, NextApiResponse } from 'next'
import { spawn } from 'child_process'
import path from 'path'
import { pushSignal, type SignalEvent, type SignalScenario } from './signal-store'

// Stub data returned when Python is not available (dev mode on Windows, etc.)
const STUB_SIGNALS: Record<SignalScenario, Omit<SignalEvent, 'scenario' | '_source'>> = {
  'supplier-cyber-incident': {
    event_id: 'sig-stub-cyber',
    event_type: 'external_signal',
    timestamp: new Date().toISOString(),
    epoch_ms: Date.now(),
    signal_category: 'CYBER_INCIDENT',
    signal_code: 'MOVEIT_STYLE_BREACH_LOGISTICS_2024',
    affected_sector: 'LOGISTICS',
    severity: 'CRITICAL',
    source_feed: 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)',
    source_channel: 'Global Cyber Threat Intelligence · Known Exploited Vulnerabilities Feed',
    headline:
      'Cyber Threat Advisory (CVE-2023-34362): Ransomware incident confirmed at a tier-2 logistics supplier. Managed file transfer system compromised — supplier cannot process orders, issue invoices, or communicate shipment status. Pattern consistent with MOVEit-style zero-day vulnerability. Affected organisations include freight forwarders across the UK, France, and Benelux.',
    detail_url: 'https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-187a',
    temp_celsius: null,
    ticker_symbol: null,
    price_change_pct: null,
    injected: true,
  },
  'eu-wildfire': {
    event_id: 'sig-stub-wildfire',
    event_type: 'external_signal',
    timestamp: new Date().toISOString(),
    epoch_ms: Date.now(),
    signal_category: 'LOGISTICS_DISRUPTION',
    signal_code: 'EU_WILDFIRE_ROAD_CLOSURE_2026',
    affected_sector: 'LOGISTICS',
    severity: 'CRITICAL',
    source_feed: 'Route & Travel Disruption Intelligence',
    source_channel: 'Freight Corridor & Road Network Monitor (Google Maps Directions / National Rail style)',
    headline:
      'Corridor Disruption Alert: Wildfires across southern France and northern Spain force closure of the A9/AP-7 freight corridor (Lyon–Barcelona). Route intelligence indicates road freight suspended indefinitely; detour via Alpine passes adds 18–24 hrs transit time.',
    detail_url:
      'https://www.euronews.com/my-europe/2026/08/13/millions-across-europe-swelter-through-a-new-wave-of-extreme-temperatures',
    temp_celsius: 43.0,
    ticker_symbol: null,
    price_change_pct: null,
    injected: true,
  },
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' })
    return
  }

  const { scenario } = req.body as { scenario: SignalScenario }
  const allowed: SignalScenario[] = ['supplier-cyber-incident', 'eu-wildfire']
  if (!allowed.includes(scenario)) {
    res.status(400).json({ error: `Unknown scenario: ${scenario}` })
    return
  }

  // Attempt to run the real Python injector.  Fall back to stub on error.
  const injectorPath = path.resolve(process.cwd(), '../event-generators/signal-injector.py')

  await new Promise<void>((resolve) => {
    const py = spawn('python3', [injectorPath, scenario, '--output', 'json'], {
      cwd: path.resolve(process.cwd(), '..'),
    })

    let stdout = ''
    let stderr = ''
    py.stdout.on('data', (d: Buffer) => (stdout += d.toString()))
    py.stderr.on('data', (d: Buffer) => (stderr += d.toString()))

    py.on('close', (code) => {
      if (code === 0 && stdout.trim()) {
        try {
          const parsed = JSON.parse(stdout.trim())
          const result = {
            ...parsed,
            scenario,
            _source: 'live' as const,
          }
          pushSignal(result as SignalEvent)
          res.status(200).json(result)
        } catch {
          const result = {
            ...(STUB_SIGNALS[scenario] ?? {}),
            scenario,
            _source: 'stub' as const,
            _reason: 'parse_error',
          }
          pushSignal(result as SignalEvent)
          res.status(200).json(result)
        }
      } else {
        // Python not available or path doesn't exist yet — return stub
        const result = {
          ...(STUB_SIGNALS[scenario] ?? {}),
          scenario,
          _source: 'stub' as const,
          _reason: stderr.slice(0, 200) || `exit code ${code}`,
        }
        pushSignal(result as SignalEvent)
        res.status(200).json(result)
      }
      resolve()
    })

    py.on('error', () => {
      const result = {
        ...(STUB_SIGNALS[scenario] ?? {}),
        scenario,
        _source: 'stub' as const,
        _reason: 'python_not_found',
      }
      pushSignal(result as SignalEvent)
      res.status(200).json(result)
      resolve()
    })
  })
}
