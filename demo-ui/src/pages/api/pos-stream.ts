/**
 * GET /api/pos-stream
 *
 * Server-Sent Events endpoint. Emits synthetic POS transaction events at
 * roughly 1 event/second. When the demo is wired to a real Iceberg table
 * the implementation can be swapped here — the client component is unchanged.
 *
 * Each SSE message is JSON matching the RetailPosEvent shape from
 * event-generators/shared/event_schema.py (snake_case kept for consistency).
 */

import type { NextApiRequest, NextApiResponse } from 'next'

const STORES = [
  'STR-LON-001', 'STR-LON-002', 'STR-LON-003', 'STR-LON-004', 'STR-LON-005',
  'STR-EME-001', 'STR-EME-002', 'STR-EME-003', 'STR-EME-004',
  'STR-EME-005', 'STR-EME-006', 'STR-EME-007', 'STR-EME-008',
]

const SKUS: [string, number, string][] = [
  ['SKU-PRO-MAX-01',        899.00, 'TECHNOLOGY'],
  ['SKU-ENERGY-BAR-12',       2.50, 'FOOD_BEVERAGE'],
  ['SKU-WIRELESS-EAR-04',   129.99, 'TECHNOLOGY'],
  ['SKU-ORGANIC-MILK-01',     1.85, 'FOOD_BEVERAGE'],
  ['SKU-SMART-WATCH-09',    299.00, 'TECHNOLOGY'],
  ['SKU-PREMIUM-COFFEE-02',   8.95, 'FOOD_BEVERAGE'],
  ['SKU-RUNNING-SHOE-07',   159.99, 'FASHION'],
  ['SKU-YOGA-MAT-03',        39.99, 'CONSUMER_LEISURE'],
  ['SKU-DESK-LAMP-11',       49.99, 'HOME_GOODS'],
  ['SKU-MOTOR-OIL-05',       18.50, 'AUTOMOTIVE'],
]

const PAYMENT_METHODS = ['Contactless', 'Visa', 'Mastercard', 'ApplePay', 'GooglePay']

function rand(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function generatePosEvent() {
  const store = pick(STORES)
  const [sku, price, sector] = pick(SKUS)
  const qty = rand(1, 4)
  const ts = new Date().toISOString()
  return {
    event_id: `pos-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    event_type: 'pos_transaction',
    timestamp: ts,
    epoch_ms: Date.now(),
    transaction_id: `TXN-${rand(1000000, 9999999)}`,
    store_id: store,
    region: store.startsWith('STR-LON') ? 'UK-London' : 'EMEA',
    sku_id: sku,
    sector,
    quantity: qty,
    unit_price: price,
    total_amount: Math.round(qty * price * 100) / 100,
    payment_method: pick(PAYMENT_METHODS),
    inventory_remaining_estimate: rand(5, 120),
  }
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  // SSE headers
  res.setHeader('Content-Type', 'text/event-stream; charset=utf-8')
  res.setHeader('Cache-Control', 'no-cache, no-transform')
  res.setHeader('Connection', 'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')   // Nginx: disable buffering
  res.flushHeaders()

  const send = (event: object) => {
    res.write(`data: ${JSON.stringify(event)}\n\n`)
  }

  // Emit immediately so the client doesn't wait
  send(generatePosEvent())

  const interval = setInterval(() => {
    // Vary rate slightly for realism
    send(generatePosEvent())
  }, rand(700, 1400))

  req.on('close', () => {
    clearInterval(interval)
    res.end()
  })
}

// Opt out of Next.js body parsing for SSE
export const config = {
  api: { bodyParser: false },
}
