# Demo UI — README
# watsonx.data on IBM Power — Presales Demo UI

## Overview

Next.js / Carbon Design System dashboard for the IBM watsonx.data on IBM Power presales demo.
Deployed on the RHEL/Power10 sidecar VM.  Carbon G100 dark theme throughout.

## Panels

| Panel | Location | Description |
|---|---|---|
| **Live POS Stream** | Top-left | SSE-driven scrolling POS transactions. Connects to `/api/pos-stream`. Real Iceberg table swap-in requires only updating that API route. |
| **Signal Control** | Top-right | Fire the two primary demo arc scenarios: `supplier-cyber-incident` and `eu-wildfire`. Each calls `/api/inject-signal` which runs `signal-injector.py`. |
| **Sidecar Alerts** | Bottom-left | Federated query result cards. Appear immediately after a signal fires. The cyber card renders the `NOT VISIBLE IN ERP WITHOUT FEDERATION` punchline prominently. |
| **Data Sources** | Bottom-right | Architecture talking point. IBM i / EDB Postgres / Iceberg — status indicators, table names, presenter narrative for each source. |

## Quick start (local dev — Windows)

```powershell
cd demo-ui
npm install
npm run dev
# → http://localhost:3000
```

## Deploy to RHEL VM

```bash
# From repo root on your local machine:
bash demo-ui/deploy-demo-ui.sh \
  --host pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com \
  --user ec2-user \
  --key "C:/Users/029878866/Downloads/user_ssh_private_key (1).user"
```

The script:
1. rsyncs `demo-ui/` and `event-generators/` to the VM
2. Runs `npm install` + `npm run build`
3. Starts the app under PM2 (auto-restart on crash / reboot)
4. Writes an Nginx reverse-proxy config to `/tmp/nginx-demo-ui.conf`

After deploy: `http://pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com:3000`

## Manual deploy (SSH)

```bash
# On the RHEL VM:
cd ~/watsonx-data-power-demo/demo-ui
npm install
npm run build

# Start:
PORT=3000 pm2 start npm --name demo-ui -- start
pm2 save
```

## Wiring to real Iceberg / EDB (post-setup)

### POS stream
Replace `src/pages/api/pos-stream.ts` with a Presto/watsonx.data query against
`iceberg_data2.retail.retail_pos_events` — use `epoch_ms > ?` with a watermark to
emit only new rows.

### Signal injection
`signal-injector.py` already writes to stdout as JSON.  To write to Iceberg,
pipe its output into the Iceberg writer (see `setup/2-configure-federation.md`).
The `inject-signal.ts` API already calls `signal-injector.py` via subprocess — 
no UI changes needed once the Python script writes to Iceberg.

### Alert cards
The federated queries in `queries/retail/` return exactly the fields the alert
cards render.  Replace the `_alert` stub in `inject-signal.ts` with a Presto
query result once EDB is installed and federation is configured.

## Architecture

```
Browser
  └── Next.js (RHEL VM, port 3000)
        ├── GET  /api/pos-stream       → SSE (synthetic → real Iceberg swap-in)
        ├── POST /api/inject-signal    → runs signal-injector.py (Python subprocess)
        └── GET  /api/alerts           → in-memory store (populated by inject-signal)

signal-injector.py
  └── writes ExternalSignalEvent JSON → stdout (→ Iceberg when wired)

AI sidecar (future)
  └── polls Iceberg retail_signals every N seconds
  └── on CRITICAL signal → fires federated query (cyber or wildfire SQL)
  └── pushes result → /api/alerts store (or Iceberg results table)
```

## Demo arc (presenter sequence)

1. Open http://VM:3000 — live POS stream is already scrolling
2. Walk through Data Sources panel (bottom-right) — "three sources, joined in real time"
3. Click **⚡ Fire Signal → Supplier Cyber Incident**
   - Alert card 1 appears bottom-left
   - Point to `erp_visibility = NOT VISIBLE IN ERP WITHOUT FEDERATION`
   - *"Your ERP has never heard of these companies."*
4. Click **⚡ Fire Signal → EU Wildfire**
   - Alert card 2 appears alongside card 1
   - Point to AT_RISK_POs (POs that can't move) + DEMAND_SPIKE SKUs
   - *"This fire broke out at 6am. Your weekly freight report was printed last Friday."*
5. Pause. *"A static map cannot tell you either of those things."*
