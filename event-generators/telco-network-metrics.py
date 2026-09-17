#!/usr/bin/env python3
"""
Telco Network Metrics Streaming Event Generator
Simulates cell tower telemetry to demonstrate real-time network health analytics,
degradation anomaly detection, and correlation with customer service records.
"""

import argparse
import random
import sys
import time
import uuid
from pathlib import Path

# Add shared path
sys.path.append(str(Path(__file__).parent))
from shared.event_schema import TelcoMetricEvent, current_iso_time, current_epoch_ms

REGIONS = ["London-Metro", "Midlands", "Manchester-Urban", "Scotland-Highlands", "Wales-Rural"]
TOWERS = [f"TWR-{region[:3].upper()}-{i:03d}" for region in REGIONS for i in range(1, 25)]

def generate_event(inject_anomaly: bool = False) -> TelcoMetricEvent:
    tower = random.choice(TOWERS)
    region = next(r for r in REGIONS if tower.startswith(f"TWR-{r[:3].upper()}"))
    
    if inject_anomaly:
        signal = round(random.uniform(-115.0, -100.0), 1)
        latency = random.randint(180, 520)
        packet_loss = round(random.uniform(2.5, 8.5), 2)
        active_users = random.randint(800, 3500)
        cpu_util = round(random.uniform(85.0, 99.5), 1)
        status = "DEGRADED"
    else:
        signal = round(random.uniform(-85.0, -65.0), 1)
        latency = random.randint(15, 65)
        packet_loss = round(random.uniform(0.01, 0.4), 2)
        active_users = random.randint(50, 1200)
        cpu_util = round(random.uniform(20.0, 65.0), 1)
        status = "HEALTHY"

    return TelcoMetricEvent(
        event_id=f"evt-{uuid.uuid4().hex[:10]}",
        event_type="network_telemetry",
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        tower_id=tower,
        region=region,
        signal_strength_dbm=signal,
        latency_ms=latency,
        packet_loss_pct=packet_loss,
        active_users=active_users,
        cpu_util_pct=cpu_util,
        status=status
    )

def main():
    parser = argparse.ArgumentParser(description="Telco Network Metrics Generator")
    parser.add_argument("--rate", type=float, default=5.0, help="Events per second (default: 5)")
    parser.add_argument("--duration", type=int, default=30, help="Runtime duration in seconds (0 for indefinite)")
    parser.add_argument("--anomalies", action="store_true", help="Periodically inject network degradation anomalies")
    parser.add_argument("--output", choices=["console", "json"], default="console", help="Output format")
    args = parser.parse_args()

    interval = 1.0 / max(0.1, args.rate)
    start_time = time.time()
    count = 0

    print(f">> [Telco Event Streamer] Starting stream at {args.rate} evt/sec...")
    if args.anomalies:
        print("[!] Anomaly injection ENABLED (simulating weather/hardware degradation).")

    try:
        while True:
            is_anomaly = args.anomalies and (random.random() < 0.12)
            event = generate_event(inject_anomaly=is_anomaly)
            count += 1
            
            if args.output == "json":
                print(event.to_json())
            else:
                prefix = "[DEGRADED]" if event.status == "DEGRADED" else "[HEALTHY] "
                print(f"{prefix} Tower: {event.tower_id:18} | Region: {event.region:16} | Latency: {event.latency_ms:3}ms | Loss: {event.packet_loss_pct:4.2f}% | Signal: {event.signal_strength_dbm}dBm")

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"\n>> Stream completed. Emitted {count} telemetry events.")

if __name__ == "__main__":
    main()
