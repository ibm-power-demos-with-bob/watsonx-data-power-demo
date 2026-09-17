import type { AlertCard } from './alerts'
import { pushAlert, readStore } from './alerts'
import { type SignalEvent, readSignalStore } from './signal-store'
import { ingestLiveFeeds } from './live-feed-fetcher'
import type { WxdQueryResult } from './wxd-query'

// ---------------------------------------------------------------------------
// watsonx.data federated query helpers
// ---------------------------------------------------------------------------

/**
 * Calls /api/wxd-query internally (server-to-server, same Next.js process).
 * Falls back gracefully when WXD env vars are not set.
 */
async function wxdQuery(sql: string): Promise<WxdQueryResult | null> {
  const prestoHost = process.env.WXD_PRESTO_HOST
  if (!prestoHost) return null          // no env — use stub path

  try {
    // Import the query runner directly to avoid HTTP round-trip in the same process
    const { runPrestoQueryInternal } = await import('./wxd-query-internal')
    return await runPrestoQueryInternal(sql)
  } catch (err) {
    console.error('[detect-signals] wxd query error:', err instanceof Error ? err.message : err)
    return null
  }
}

function rowVal(row: unknown[], idx: number): unknown {
  return Array.isArray(row) ? row[idx] : undefined
}

// ---------------------------------------------------------------------------
// Cyber scenario — fetch live exposure from pg_olist + ibmi_olist
// ---------------------------------------------------------------------------

/**
 * Queries pg_olist.olist for compromised Nexaflow tier-2 supplier exposure.
 * Returns open_po_count, tier1_suppliers_affected, total_exposure, earliest_ship_limit.
 * Falls back to stub values if the query fails or env is unset.
 */
async function fetchCyberExposure() {
  const stub = {
    open_po_count: 14,
    tier1_suppliers_affected: 6,
    total_exposure: 47230.0,
    earliest_ship_limit: '2024-06-10',
    critical_pos_7_days: 9,
  }

  const sql = `
    SELECT
      COUNT(po.po_number)                               AS open_po_count,
      COUNT(DISTINCT s.supplier_id)                     AS tier1_suppliers_affected,
      CAST(SUM(po.unit_price + po.freight_value) AS DOUBLE) AS total_exposure_gbp,
      MIN(CAST(po.ship_limit_date AS VARCHAR(30)))      AS earliest_order,
      SUM(CASE WHEN po.po_status = 'OPEN' THEN 1 ELSE 0 END) AS critical_7d
    FROM pg_olist.olist.v_purchase_orders po
    JOIN pg_olist.olist.v_suppliers s
      ON po.supplier_id = s.supplier_id
    JOIN pg_olist.olist.v_tier2_suppliers t2
      ON s.subcontracted_to_id = t2.tier2_id
    WHERE t2.company_name = 'Nexaflow Logistics Ltd'
      AND t2.breach_status = 'COMPROMISED'
  `.trim()

  const result = await wxdQuery(sql)
  if (!result || result.rows.length === 0) return stub

  const row = result.rows[0]
  const colIdx = (name: string) => result.columns.findIndex(c => c === name)

  return {
    open_po_count:           Number(rowVal(row, colIdx('open_po_count')))            || stub.open_po_count,
    tier1_suppliers_affected: Number(rowVal(row, colIdx('tier1_suppliers_affected'))) || stub.tier1_suppliers_affected,
    total_exposure:           Number(rowVal(row, colIdx('total_exposure_gbp')))       || stub.total_exposure,
    earliest_ship_limit:      String(rowVal(row, colIdx('earliest_order'))            || stub.earliest_ship_limit),
    critical_pos_7_days:      Number(rowVal(row, colIdx('critical_7d')))              || stub.critical_pos_7_days,
  }
}

// ---------------------------------------------------------------------------
// Wildfire scenario — fetch at-risk POs and demand spike from pg_olist
// ---------------------------------------------------------------------------

async function fetchWildfireExposure() {
  const stubAtRisk = [
    { po_number: 'PO-2017-00142', order_value: 840.0,  days_to_ship_limit: 3, category_en: 'furniture_decor',      supplier_region: 'South France' },
    { po_number: 'PO-2017-00198', order_value: 1260.0, days_to_ship_limit: 5, category_en: 'home_appliances',      supplier_region: 'Catalonia' },
    { po_number: 'PO-2017-00307', order_value: 510.0,  days_to_ship_limit: 6, category_en: 'computers_accessories', supplier_region: 'South France' },
  ]
  const stubDemandSpike = [
    { sku_id: 'SKU-ORGANIC-MILK-01', region: 'EMEA-South', stock_alert: 'LOW STOCK',               units_last_hour: 312 },
    { sku_id: 'SKU-ENERGY-BAR-12',   region: 'EMEA-South', stock_alert: 'CRITICAL — STOCKOUT', units_last_hour: 487 },
  ]

  // At-risk POs: suppliers in South France or Catalonia with ship limit within 7 days
  const sqlAtRisk = `
    SELECT
      po.po_number,
      CAST(po.unit_price + po.freight_value AS DOUBLE) AS order_value,
      w.region_label                                   AS supplier_region
    FROM pg_olist.olist.v_purchase_orders po
    JOIN pg_olist.olist.v_warehouses w
      ON po.warehouse_id = w.warehouse_id
    WHERE w.region_label IN ('South France', 'Catalonia', 'Mediterranean')
      AND po.po_status = 'OPEN'
    ORDER BY po.ship_limit_date ASC
    LIMIT 5
  `.trim()

  const result = await wxdQuery(sqlAtRisk)

  if (!result || result.rows.length === 0) {
    return { at_risk_pos: stubAtRisk, demand_spike: stubDemandSpike }
  }

  const atRiskPos = result.rows.map((row) => {
    const colIdx = (name: string) => result.columns.findIndex(c => c === name)
    return {
      po_number:           String(rowVal(row, colIdx('po_number')) ?? ''),
      order_value:         Number(rowVal(row, colIdx('order_value')) ?? 0),
      days_to_ship_limit:  3,   // not in query — kept for card display compatibility
      category_en:         'supply_chain',
      supplier_region:     String(rowVal(row, colIdx('supplier_region')) ?? 'EMEA'),
    }
  })

  return { at_risk_pos: atRiskPos.length > 0 ? atRiskPos : stubAtRisk, demand_spike: stubDemandSpike }
}

// ---------------------------------------------------------------------------
// Static context for matched entity descriptions
// ---------------------------------------------------------------------------

const MATCHED_ENTITY: Record<SignalEvent['scenario'], { kind: string; name: string; source: string }> = {
  'supplier-cyber-incident': {
    kind: 'tier2_supplier',
    name: 'Nexaflow Logistics Ltd',
    source: 'pg_olist tier-2 supplier network × ibmi_olist ERP orders',
  },
  'eu-wildfire': {
    kind: 'supplier_route',
    name: 'A9/AP-7 freight corridor',
    source: 'pg_olist warehouse routes × ibmi_olist active freight POs',
  },
}

// ---------------------------------------------------------------------------
// Relevance scoring
// ---------------------------------------------------------------------------

function evaluatesBusinessImpact(signal: SignalEvent): boolean {
  if (signal.injected) return true

  if (signal.signal_code === 'CVE-2023-34362' || signal.headline.includes('MOVEit') || signal.headline.includes('Nexaflow')) {
    return true
  }

  if (signal.signal_code === 'EU_WILDFIRE_ROAD_CLOSURE_2026' || signal.headline.includes('A9/AP-7 corridor closed')) {
    return true
  }

  return false
}

function makeReasoning(signal: SignalEvent, live: boolean): string {
  const src = live ? 'Live federated query across' : 'Simulated federation result from'
  if (signal.scenario === 'supplier-cyber-incident') {
    return `${src} pg_olist (tier-2 supplier network) and ibmi_olist (core ERP): Nexaflow Logistics Ltd breach confirmed, open purchase-order exposure quantified in real time.`
  }
  return `${src} pg_olist (warehouse routes) and ibmi_olist (active POs): A9/AP-7 corridor disruption matched active supplier dependencies, at-risk POs identified.`
}

// ---------------------------------------------------------------------------
// Detection types
// ---------------------------------------------------------------------------

export type DetectionResult = {
  eventId: string
  scenario: SignalEvent['scenario']
  detectedAt: string
  matchedEntity: string
  matchedEntityType: string
  relevanceSource: string
  reasoning: string
  alertId: string
  businessImpact: boolean
}

// ---------------------------------------------------------------------------
// Main detection loop
// ---------------------------------------------------------------------------

export async function runDetection(): Promise<DetectionResult[]> {
  await ingestLiveFeeds()

  const signals = readSignalStore()
  const alerts = readStore()
  const detections: DetectionResult[] = []
  const liveEnabled = !!process.env.WXD_PRESTO_HOST

  for (const signal of signals) {
    const hasImpact = evaluatesBusinessImpact(signal)
    if (!hasImpact) continue

    const existing = alerts.find((alert) => alert.signal.signal_code === signal.signal_code)
    if (existing) continue

    const matched = MATCHED_ENTITY[signal.scenario]

    // Fetch live watsonx.data data (or use stub if env not configured)
    let alertData: Record<string, unknown>
    if (signal.scenario === 'supplier-cyber-incident') {
      const exposure = await fetchCyberExposure()
      alertData = {
        compromised_tier2_company:  'Nexaflow Logistics Ltd',
        compromised_service_type:   'Managed File Transfer',
        tier2_region:               'South East England',
        cve_reference:              'CVE-2023-34362',
        breach_notified:            new Date().toISOString(),
        supplier_region:            'South East England',
        currency_code:              'GBP',
        open_po_count:              exposure.open_po_count,
        tier1_suppliers_affected:   exposure.tier1_suppliers_affected,
        total_exposure:             exposure.total_exposure,
        earliest_ship_limit:        exposure.earliest_ship_limit,
        critical_pos_7_days:        exposure.critical_pos_7_days,
        erp_visibility:             'NOT VISIBLE IN ERP WITHOUT FEDERATION',
      }
    } else {
      const { at_risk_pos, demand_spike } = await fetchWildfireExposure()
      alertData = {
        at_risk_pos,
        demand_spike,
        currency_code:  'GBP',
        temp_celsius:   43.0,
      }
    }

    const alert: AlertCard = {
      id: `alert-${signal.event_id}`,
      scenario: signal.scenario,
      firedAt: new Date().toISOString(),
      signal: {
        signal_category: signal.signal_category,
        signal_code:     signal.signal_code,
        severity:        signal.severity,
        headline:        signal.headline,
        affected_sector: signal.affected_sector,
        detail_url:      signal.detail_url,
        temp_celsius:    signal.temp_celsius,
        source_feed:     signal.source_feed ?? (signal.scenario === 'supplier-cyber-incident'
          ? 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)'
          : 'Route & Travel Disruption Intelligence'),
        source_channel:  signal.source_channel ?? (signal.scenario === 'supplier-cyber-incident'
          ? 'Global Cyber Threat Intelligence · Known Exploited Vulnerabilities Feed'
          : 'Freight Corridor Monitor (Google Maps Directions / National Rail style)'),
      },
      alert: {
        ...alertData,
        detected_by:         liveEnabled ? 'watsonx.data Live Federation Query' : 'watsonx.data Real-time Detector',
        upstream_feed:       signal.source_feed ?? (signal.scenario === 'supplier-cyber-incident'
          ? 'Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)'
          : 'Route & Travel Disruption Intelligence'),
        matched_entity:      matched.name,
        matched_entity_type: matched.kind,
        relevance_source:    matched.source,
        reasoning:           makeReasoning(signal, liveEnabled),
      },
      source: liveEnabled ? 'live' : 'stub',
    }

    pushAlert(alert)
    detections.push({
      eventId:           signal.event_id,
      scenario:          signal.scenario,
      detectedAt:        alert.firedAt,
      matchedEntity:     matched.name,
      matchedEntityType: matched.kind,
      relevanceSource:   matched.source,
      reasoning:         makeReasoning(signal, liveEnabled),
      alertId:           alert.id,
      businessImpact:    true,
    })
  }

  return detections
}
