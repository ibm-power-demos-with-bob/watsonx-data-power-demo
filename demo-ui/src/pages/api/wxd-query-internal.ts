/**
 * wxd-query-internal.ts
 *
 * Internal helper that exposes the Presto HTTP query runner so that
 * detect-signals.ts can call it directly (same Node.js process) rather
 * than making an HTTP round-trip to /api/wxd-query.
 *
 * Do NOT import this from browser-side code — it uses Node.js built-ins (https, http).
 *
 * Auth modes (controlled by .env.local):
 *
 *   Developer Base Image (VMware TechZone):
 *     WXD_PRESTO_HOST=<region>.services.cloud.techzone.ibm.com
 *     WXD_PRESTO_PORT=<mapped port from reservation, e.g. 15152>
 *     WXD_PRESTO_SCHEME=https
 *     WXD_PRESTO_USER=watsonx
 *     WXD_PRESTO_PASSWORD=<password from reservation>
 *     → Uses HTTP Basic auth. No IAM, no CRN, no API key needed.
 *
 *   watsonx.data SaaS (legacy — kept for reference):
 *     WXD_PRESTO_HOST=<engine>.lakehouse.ibmappdomain.cloud
 *     WXD_PRESTO_PORT=31437
 *     WXD_PRESTO_SCHEME=https
 *     WXD_APIKEY=<ibm cloud api key>
 *     WXD_INSTANCE_CRN=crn:v1:bluemix:...
 *     → Uses IAM Bearer token exchange.
 */

import https from 'https'
import http from 'http'
import type { WxdQueryResult } from './wxd-query'

const MAX_ROWS = 500
const QUERY_TIMEOUT_MS = 90_000
const POLL_INTERVAL_MS = 500   // reduced from 1500ms — polls are cheap, latency matters for demo

function doRequest(
  url: string,
  opts: { method?: string; headers?: Record<string, string>; body?: string },
): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url)
    const isHttps = parsed.protocol === 'https:'
    const lib: typeof https = isHttps ? https : (http as unknown as typeof https)
    const reqOpts: https.RequestOptions = {
      hostname: parsed.hostname,
      port: parsed.port || (isHttps ? 443 : 80),
      path: parsed.pathname + parsed.search,
      method: opts.method ?? 'GET',
      headers: opts.headers ?? {},
      rejectUnauthorized: false,
    }
    const req = lib.request(reqOpts, (res) => {
      const chunks: Buffer[] = []
      res.on('data', (c: Buffer) => chunks.push(c))
      res.on('end', () =>
        resolve({ status: res.statusCode ?? 0, body: Buffer.concat(chunks).toString('utf8') })
      )
    })
    req.on('error', reject)
    if (opts.body) req.write(opts.body)
    req.end()
  })
}

/** Exchange an IBM Cloud API key for a short-lived IAM bearer token (SaaS path). */
async function getIamToken(apiKey: string): Promise<string> {
  const body = `grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey=${encodeURIComponent(apiKey)}`
  const resp = await doRequest('https://iam.cloud.ibm.com/identity/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' },
    body,
  })
  if (resp.status !== 200) {
    throw new Error(`IAM token exchange failed: HTTP ${resp.status}: ${resp.body.slice(0, 200)}`)
  }
  const json = JSON.parse(resp.body)
  return json.access_token as string
}

export async function runPrestoQueryInternal(sql: string): Promise<WxdQueryResult> {
  const prestoHost = process.env.WXD_PRESTO_HOST
  const prestoPort = process.env.WXD_PRESTO_PORT ?? '8443'
  const prestoScheme = process.env.WXD_PRESTO_SCHEME ?? 'https'

  if (!prestoHost) {
    throw new Error('WXD_PRESTO_HOST is not set')
  }

  // ---------------------------------------------------------------------------
  // Auth: Developer Base Image uses HTTP Basic auth with a local watsonx user.
  // SaaS uses IAM Bearer token exchange from an IBM Cloud API key.
  // Presence of WXD_PRESTO_USER selects the Basic auth path.
  // ---------------------------------------------------------------------------
  const prestoUser = process.env.WXD_PRESTO_USER
  const prestoPassword = process.env.WXD_PRESTO_PASSWORD

  let baseHeaders: Record<string, string>

  if (prestoUser) {
    // Developer Base Image — Basic auth
    const credentials = Buffer.from(`${prestoUser}:${prestoPassword ?? ''}`).toString('base64')
    baseHeaders = {
      Authorization: `Basic ${credentials}`,
      'X-Presto-User': prestoUser,
      'X-Presto-Source': 'wxd-demo-ui',
      'Content-Type': 'text/plain',
    }
  } else {
    // SaaS — IAM Bearer token
    const apiKey = process.env.WXD_APIKEY
    const instanceCrn = process.env.WXD_INSTANCE_CRN
    if (!apiKey || !instanceCrn) {
      throw new Error('Either WXD_PRESTO_USER or (WXD_APIKEY + WXD_INSTANCE_CRN) must be set')
    }
    const iamToken = await getIamToken(apiKey)
    const instanceGuid = instanceCrn.split(':').slice(-3, -2)[0] ?? ''
    baseHeaders = {
      Authorization: `Bearer ${iamToken}`,
      'X-Presto-User': 'ibmcloud',
      'X-Presto-Source': 'wxd-demo-ui',
      'Content-Type': 'text/plain',
      AuthInstanceId: instanceCrn,
      LhInstanceId: instanceGuid,
    }
  }

  // ---------------------------------------------------------------------------
  // Presto returns nextUri as an absolute URL using its own internal hostname.
  // On the Developer Base Image the nextUri host/port matches what we connected
  // to, so no rewrite is needed. On the old Satellite tunnel path (http scheme)
  // we had to rewrite poll URLs to route through the tunnel — kept here for
  // reference but not exercised in the current setup.
  // ---------------------------------------------------------------------------
  function rewriteUri(uri: string): string {
    if (prestoScheme === 'https') return uri
    try {
      const u = new URL(uri)
      u.protocol = prestoScheme + ':'
      u.hostname = prestoHost!
      u.port = prestoPort
      return u.toString()
    } catch {
      return uri
    }
  }

  const submitUrl = `${prestoScheme}://${prestoHost}:${prestoPort}/v1/statement`
  const submitResp = await doRequest(submitUrl, {
    method: 'POST',
    headers: baseHeaders,
    body: sql,
  })

  if (submitResp.status !== 200) {
    throw new Error(
      `Presto submit failed: HTTP ${submitResp.status}: ${submitResp.body.slice(0, 400)}`
    )
  }

  let state = JSON.parse(submitResp.body)
  const columns: string[] = []
  const rows: unknown[][] = []
  const deadline = Date.now() + QUERY_TIMEOUT_MS

  while (true) {
    if (Date.now() > deadline) {
      throw new Error(`Query timed out after ${QUERY_TIMEOUT_MS / 1000}s`)
    }

    if (columns.length === 0 && state.columns?.length) {
      for (const col of state.columns) columns.push(col.name as string)
    }

    if (state.data?.length && rows.length < MAX_ROWS) {
      for (const row of state.data) {
        if (rows.length >= MAX_ROWS) break
        rows.push(row as unknown[])
      }
    }

    const queryState: string = state.stats?.state ?? 'UNKNOWN'
    if (queryState === 'FINISHED') break
    if (queryState === 'FAILED') {
      const msg = state.error?.message ?? state.error?.errorName ?? JSON.stringify(state.error)
      throw new Error(`Presto query FAILED: ${msg}`)
    }

    const nextUri: string | undefined = state.nextUri
    if (!nextUri) break

    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
    const pollResp = await doRequest(rewriteUri(nextUri), { headers: baseHeaders })
    if (pollResp.status !== 200) {
      throw new Error(`Presto poll failed: HTTP ${pollResp.status}`)
    }
    state = JSON.parse(pollResp.body)
  }

  return { columns, rows }
}
