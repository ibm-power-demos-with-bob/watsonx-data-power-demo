/**
 * POST /api/wxd-query
 *
 * Executes a single SQL statement against the watsonx.data Presto engine
 * (eu-gb, instance e4ec7696-6363-4ad9-a21f-41eba7b7a663, engine prismo600).
 *
 * Uses the Presto HTTP REST protocol — delegates to wxd-query-internal.ts
 * which contains the actual polling loop.
 *
 * Environment variables (set in .env.local on the RHEL server):
 *   WXD_PRESTO_HOST  – Presto engine host, e.g. eu-gb.lakehouse.cloud.ibm.com
 *                      Do NOT include a path or trailing slash.
 *   WXD_APIKEY       – watsonx.data student service API key (from TechZone)
 *   WXD_INSTANCE_CRN – watsonx.data full CRN (used as AuthInstanceId header)
 *
 * Request body:   { sql: string }
 * Response body:  { columns: string[], rows: unknown[][] } on success
 *                 { error: string } on failure
 */

import type { NextApiRequest, NextApiResponse } from 'next'

export type WxdQueryResult = {
  columns: string[]
  rows: unknown[][]
}

export type WxdQueryError = {
  error: string
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<WxdQueryResult | WxdQueryError>,
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    res.status(405).json({ error: 'Method not allowed — use POST' })
    return
  }

  const { sql } = req.body as { sql?: string }
  if (!sql || typeof sql !== 'string' || !sql.trim()) {
    res.status(400).json({ error: 'Missing or empty sql in request body' })
    return
  }

  const prestoHost = process.env.WXD_PRESTO_HOST
  const apiKey = process.env.WXD_APIKEY
  const instanceCrn = process.env.WXD_INSTANCE_CRN

  if (!prestoHost || !apiKey || !instanceCrn) {
    const missing = [
      !prestoHost && 'WXD_PRESTO_HOST',
      !apiKey && 'WXD_APIKEY',
      !instanceCrn && 'WXD_INSTANCE_CRN',
    ]
      .filter(Boolean)
      .join(', ')
    res.status(500).json({ error: `Server misconfigured — missing env vars: ${missing}` })
    return
  }

  try {
    const { runPrestoQueryInternal } = await import('./wxd-query-internal')
    const result = await runPrestoQueryInternal(sql.trim())
    res.status(200).json(result)
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[wxd-query] Error:', msg)
    res.status(500).json({ error: msg })
  }
}
