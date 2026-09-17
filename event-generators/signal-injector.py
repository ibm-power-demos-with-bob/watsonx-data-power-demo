#!/usr/bin/env python3
"""
event-generators/signal-injector.py
=====================================
Demo signal injector — fires a pre-crafted external signal event into the
Iceberg retail_pos_events stream to demonstrate the "satnav" real-time
reaction narrative.

Two primary demo arc scenarios (both reference real, documented, politically
neutral events):

  supplier-cyber-incident
    Reference: MOVEit Transfer vulnerability (CVE-2023-34362), June 2023 —
    a zero-day SQL injection in a widely-used managed file transfer tool
    affected thousands of organisations globally across every sector,
    including logistics, retail supply chains, and financial services.
    The narrative hook: the breach hits a TIER-2 supplier — one your ERP
    knows nothing about directly.  Only federation across both the core ERP
    (IBM i / Source 1) and the operational supplier network (Source 2)
    reveals the exposure.  Safe to reference; no political dimension.

  eu-wildfire
    Reference: European Summer 2025/2026 extreme heat → wildfires across
    southern France, Iberia, Greece.  Wildfire closes the A9/AP-7 road
    corridor (Lyon–Barcelona freight route).  Sudden, unforeseeable —
    the point being it CANNOT be forecast, unlike a heatwave.
    Affects LOGISTICS-sector suppliers (road-freight-dependent POs).
    Backdrop: Euronews, August 2026 — https://www.euronews.com/my-europe/2026/08/13/millions-across-europe-swelter-through-a-new-wave-of-extreme-temperatures

Additional scenarios (not in the default demo arc — available if relevant):

  eu-heatwave
    Demoted to secondary: the prolonged heat is the *cause* of the wildfire,
    not itself a reaction trigger.  Useful for cold-chain / FOOD_BEVERAGE
    demand-spike narrative if the audience is in that sector.

  port-closure, energy-price-spike
    Ready to use for logistics/manufacturing verticals.

The injected event appears as an ExternalSignalEvent row in the same Iceberg
table as the live POS stream.  The AI sidecar's continuous scoring loop picks
it up on the next poll cycle and fires the appropriate federated alert query.

Usage
-----
  # Fire the supplier cyber incident signal (single shot):
  python event-generators/signal-injector.py supplier-cyber-incident

  # Fire the EU wildfire / road corridor closure signal:
  python event-generators/signal-injector.py eu-wildfire

  # Preview what would be injected (no write):
  python event-generators/signal-injector.py supplier-cyber-incident --dry-run

  # Output JSON only (for piping into another process or Iceberg writer):
  python event-generators/signal-injector.py eu-wildfire --output json

  # Run a live background stream THEN inject after N seconds (full demo arc):
  python event-generators/signal-injector.py supplier-cyber-incident \\
    --with-stream --stream-duration 20

Notes
-----
  Writing to a real Iceberg table requires the COS / watsonx.data writer to
  be wired up (see setup/2-configure-federation.md).  Until that is in place,
  --output json emits the event as JSON on stdout — useful for testing the
  sidecar logic independently.
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from shared.event_schema import ExternalSignalEvent, RetailPosEvent, current_iso_time, current_epoch_ms

# ─────────────────────────────────────────────────────────────────────────────
# Pre-crafted signal scenarios
# Each dict maps directly onto ExternalSignalEvent fields (minus event_id /
# timestamp / epoch_ms which are generated at injection time).
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS: dict[str, dict] = {

    "supplier-cyber-incident": {
        "event_type":        "external_signal",
        "signal_category":   "CYBER_INCIDENT",
        "signal_code":       "MOVEIT_STYLE_BREACH_LOGISTICS_2024",
        "affected_sector":   "LOGISTICS",
        "severity":          "CRITICAL",
        "source_feed":       "Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)",
        "source_channel":    "Global Cyber Threat Intelligence · Known Exploited Vulnerabilities Feed",
        "headline":          (
            "Cyber Threat Advisory (CVE-2023-34362): Ransomware incident confirmed at a tier-2 logistics supplier. "
            "Managed file transfer system compromised — supplier cannot "
            "process orders, issue invoices, or communicate shipment status. "
            "Pattern consistent with MOVEit-style zero-day vulnerability. "
            "Affected organisations include freight forwarders across the "
            "UK, France, and Benelux."
        ),
        "detail_url":        "https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-187a",
        "temp_celsius":      None,
        "ticker_symbol":     None,
        "price_change_pct":  None,
        "injected":          True,
        # Presenter talking point:
        # "The live Cyber Threat Intelligence feed streams known exploited vulnerability alerts directly into watsonx.data.
        #  Your procurement team knows your direct suppliers in ERP, but this
        #  threat hit a tier-2 supplier in your logistics network (Source 2).
        #  watsonx.data joins the live threat stream against EDB and IBM i in seconds."
    },

    # ── Retired primary scenario — kept for reference / finance audiences ──
    "ibm-profit-warning": {
        "event_type":        "external_signal",
        "signal_category":   "MARKET_EVENT",
        "signal_code":       "IBM_PROFIT_WARNING_Q2_2024",
        "affected_sector":   "TECHNOLOGY",
        "severity":          "HIGH",
        "headline":          (
            "IBM Q2 2024 profit warning: shares fall ~25%. "
            "Enterprise software sector selloff — Microsoft, SAP, Accenture "
            "all down. Discretionary tech spend under immediate pressure."
        ),
        "detail_url":        "https://www.ft.com/content/83aa00c5-e773-47be-b76d-5e15ea43eb3a",
        "temp_celsius":      None,
        "ticker_symbol":     "IBM",
        "price_change_pct":  -25.0,
        "injected":          True,
        # Retired from default demo arc — replaced by supplier-cyber-incident.
        # Still usable for finance/tech audiences where a market signal story
        # lands better than a cyber story.
    },

    "eu-wildfire": {
        "event_type":        "external_signal",
        "signal_category":   "LOGISTICS_DISRUPTION",
        "signal_code":       "EU_WILDFIRE_ROAD_CLOSURE_2026",
        "affected_sector":   "LOGISTICS",
        "severity":          "CRITICAL",
        "source_feed":       "Route & Travel Disruption Intelligence",
        "source_channel":    "Freight Corridor & Road Network Monitor (Google Maps Directions / National Rail style)",
        "headline":          (
            "Corridor Disruption Alert: Wildfires across southern France and northern Spain force closure "
            "of the A9/AP-7 freight corridor (Lyon–Barcelona). Route intelligence indicates road freight "
            "suspended indefinitely; detour via Alpine passes adds 18–24 hrs transit time. "
            "Affected: all road-freight POs routing through southern France."
        ),
        "detail_url":        "https://www.euronews.com/my-europe/2026/08/13/millions-across-europe-swelter-through-a-new-wave-of-extreme-temperatures",
        "temp_celsius":      43.0,
        "ticker_symbol":     None,
        "price_change_pct":  None,
        "injected":          True,
        # Presenter talking point:
        # "Live route intelligence reported the corridor closure at 7am.
        #  Your weekly freight report was printed last Friday.
        #  watsonx.data identifies at-risk POs and triggers rerouting before business opens."
        #  corridor, all due within the week, and surfaced the re-routing cost
        #  impact before your logistics team had finished their morning coffee."
    },

    # ── Additional scenarios (available, not in the primary demo arc) ──

    "eu-heatwave": {
        "event_type":        "external_signal",
        "signal_category":   "WEATHER_EVENT",
        "signal_code":       "EU_HEATWAVE_SUMMER_2025",
        "affected_sector":   "FOOD_BEVERAGE",        # demand spike angle — cold chain
        "severity":          "HIGH",
        "headline":          (
            "European heatwave summer 2025: record temperatures across UK, "
            "France, Spain, Italy.  Demand spike for chilled/refrigerated goods. "
            "Cold-chain capacity at risk.  Use for FOOD_BEVERAGE sector audiences."
        ),
        "detail_url":        "https://science.nasa.gov/earth/europes-scorching-summer/",
        "temp_celsius":      42.0,
        "ticker_symbol":     None,
        "price_change_pct":  None,
        "injected":          True,
        # Demoted to secondary — the prolonged heat is the CAUSE of the wildfire.
        # Best used for cold-chain / food retail audiences where the demand-spike
        # angle is more relevant than the logistics disruption angle.
    },

    "port-closure": {
        "event_type":        "external_signal",
        "signal_category":   "LOGISTICS_DISRUPTION",
        "signal_code":       "PORT_CLOSURE_ROTTERDAM_2025",
        "affected_sector":   "LOGISTICS",
        "severity":          "CRITICAL",
        "headline":          (
            "Rotterdam port industrial action: partial closure expected 48–72 hrs. "
            "Approximately 14% of European container throughput affected."
        ),
        "detail_url":        "",
        "temp_celsius":      None,
        "ticker_symbol":     None,
        "price_change_pct":  None,
        "injected":          True,
    },

    "energy-price-spike": {
        "event_type":        "external_signal",
        "signal_category":   "MARKET_EVENT",
        "signal_code":       "EU_ENERGY_PRICE_SPIKE_2025",
        "affected_sector":   "MANUFACTURING",
        "severity":          "MEDIUM",
        "headline":          (
            "European wholesale electricity prices spike 40% overnight "
            "following reduced wind generation and high summer demand. "
            "Energy-intensive manufacturing under margin pressure."
        ),
        "detail_url":        "",
        "temp_celsius":      None,
        "ticker_symbol":     None,
        "price_change_pct":  None,
        "injected":          True,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Signal builder
# ─────────────────────────────────────────────────────────────────────────────

def build_signal(scenario_key: str) -> ExternalSignalEvent:
    s = SCENARIOS[scenario_key]
    return ExternalSignalEvent(
        event_id=f"sig-{uuid.uuid4().hex[:10]}",
        event_type=s["event_type"],
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        signal_category=s["signal_category"],
        signal_code=s["signal_code"],
        affected_sector=s["affected_sector"],
        severity=s["severity"],
        headline=s["headline"],
        detail_url=s["detail_url"],
        temp_celsius=s["temp_celsius"],
        ticker_symbol=s["ticker_symbol"],
        price_change_pct=s["price_change_pct"],
        injected=s["injected"],
        source_feed=s.get("source_feed"),
        source_channel=s.get("source_channel"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Background POS stream (the "live stream" that runs before the trigger fires)
# ─────────────────────────────────────────────────────────────────────────────

import random

STORES  = [f"STR-EME-{i:03d}" for i in range(1, 15)] + \
          [f"STR-LON-{i:03d}" for i in range(1, 8)]
SKUS    = [
    ("SKU-PRO-MAX-01",       899.00),
    ("SKU-ENERGY-BAR-12",      2.50),
    ("SKU-WIRELESS-EAR-04",  129.99),
    ("SKU-ORGANIC-MILK-01",    1.85),
    ("SKU-SMART-WATCH-09",   299.00),
    ("SKU-PREMIUM-COFFEE-02",  8.95),
]

def emit_pos_event(output: str):
    store = random.choice(STORES)
    sku, price = random.choice(SKUS)
    qty   = random.randint(1, 4)
    event = RetailPosEvent(
        event_id=f"pos-{uuid.uuid4().hex[:10]}",
        event_type="pos_transaction",
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        transaction_id=f"TXN-{random.randint(1000000, 9999999)}",
        store_id=store,
        region="EMEA",
        sku_id=sku,
        quantity=qty,
        unit_price=price,
        total_amount=round(qty * price, 2),
        payment_method=random.choice(["Contactless", "Visa", "Mastercard", "ApplePay"]),
        inventory_remaining_estimate=random.randint(15, 120),
    )
    if output == "json":
        print(event.to_json())
    else:
        print(f"  [POS]    {event.store_id} | {event.sku_id:22} | "
              f"Qty: {event.quantity} | £{event.total_amount:6.2f} | "
              f"Stock: {event.inventory_remaining_estimate:3}")


# ─────────────────────────────────────────────────────────────────────────────
# Console rendering of the injected signal
# ─────────────────────────────────────────────────────────────────────────────

def render_signal_card(signal: ExternalSignalEvent):
    sev_prefix = {
        "CRITICAL": "🔴 CRITICAL",
        "HIGH":     "🟠 HIGH    ",
        "MEDIUM":   "🟡 MEDIUM  ",
        "LOW":      "🟢 LOW     ",
    }.get(signal.severity, signal.severity)

    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print(f"  ║  EXTERNAL SIGNAL DETECTED — {sev_prefix}                  ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    print(f"  ║  Code     : {signal.signal_code:<50} ║")
    print(f"  ║  Category : {signal.signal_category:<50} ║")
    print(f"  ║  Sector   : {signal.affected_sector:<50} ║")
    if signal.ticker_symbol:
        print(f"  ║  Ticker   : {signal.ticker_symbol}  "
              f"Change: {signal.price_change_pct:+.1f}%{'':<35} ║")
    if signal.temp_celsius:
        print(f"  ║  Peak Temp: {signal.temp_celsius}°C{'':<48} ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    # Word-wrap headline at ~58 chars
    words = signal.headline.split()
    line, lines = "", []
    for w in words:
        if len(line) + len(w) + 1 > 58:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    for l in lines:
        print(f"  ║  {l:<60} ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    print(f"  ║  ⚡ Sidecar firing federated alert query ...               ║")
    print(f"  ║  → Scanning IBM i OLIST.ORDERITEMS for {signal.affected_sector:<20} ║")
    print(f"  ║    supplier exposure                                        ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inject a pre-crafted external signal into the demo event stream."
    )
    parser.add_argument(
        "scenario",
        choices=list(SCENARIOS.keys()),
        help="Which signal scenario to inject",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the event JSON and card without writing to any stream",
    )
    parser.add_argument(
        "--output", choices=["console", "json"], default="console",
        help="console = formatted card; json = raw JSON (default: console)",
    )
    parser.add_argument(
        "--with-stream", action="store_true",
        help="Emit a live POS background stream before firing the signal",
    )
    parser.add_argument(
        "--stream-duration", type=int, default=20,
        help="Seconds of background POS stream to emit before the signal (default: 20)",
    )
    parser.add_argument(
        "--stream-rate", type=float, default=3.0,
        help="POS events per second during background stream (default: 3.0)",
    )
    args = parser.parse_args()

    signal = build_signal(args.scenario)

    if args.dry_run:
        print("-- DRY RUN — event not written to stream --")
        print(signal.to_json())
        render_signal_card(signal)
        return

    # 1. Optional background POS stream (the "calm before the storm")
    if args.with_stream:
        interval = 1.0 / max(0.1, args.stream_rate)
        deadline = time.time() + args.stream_duration
        print(f">> [POS Stream] Running for {args.stream_duration}s at "
              f"{args.stream_rate} txn/sec — signal fires after stream ends ...\n")
        while time.time() < deadline:
            emit_pos_event(args.output)
            time.sleep(interval)
        print()

    # 2. Fire the signal
    if args.output == "json":
        print(signal.to_json())
    else:
        render_signal_card(signal)

    # 3. Emit the raw JSON for any downstream consumer regardless of output mode
    #    (so the caller can pipe or redirect it)
    if args.output == "console":
        print(f">> Signal JSON: {signal.to_json()}")


if __name__ == "__main__":
    main()
