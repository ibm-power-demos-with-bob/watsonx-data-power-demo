#!/usr/bin/env python3
"""
Retail Point-of-Sale (POS) Streaming Event Generator
Simulates nationwide multi-store checkouts to showcase live stockout detection
and in-place federation with warehouse replenishment data on IBM Power.
"""

import argparse
import random
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from shared.event_schema import RetailPosEvent, current_iso_time, current_epoch_ms

REGIONS = ["EMEA-North", "EMEA-South", "Americas-East", "Americas-West", "APAC"]
STORES = [f"STR-{r[:3].upper()}-{i:03d}" for r in REGIONS for i in range(1, 30)]
SKUS = [
    ("SKU-PRO-MAX-01", 899.00),
    ("SKU-ENERGY-BAR-12", 2.50),
    ("SKU-WIRELESS-EAR-04", 129.99),
    ("SKU-ORGANIC-MILK-01", 1.85),
    ("SKU-SMART-WATCH-09", 299.00),
    ("SKU-PREMIUM-COFFEE-02", 8.95)
]

def generate_event(simulate_stockout_risk: bool = False) -> RetailPosEvent:
    store = random.choice(STORES)
    region = next(r for r in REGIONS if store.startswith(f"STR-{r[:3].upper()}"))
    sku, price = random.choice(SKUS)
    qty = random.randint(1, 4)
    total = round(qty * price, 2)
    
    if simulate_stockout_risk:
        inventory_rem = random.randint(0, 3)
    else:
        inventory_rem = random.randint(15, 120)

    return RetailPosEvent(
        event_id=f"pos-{uuid.uuid4().hex[:10]}",
        event_type="pos_transaction",
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        transaction_id=f"TXN-{random.randint(1000000, 9999999)}",
        store_id=store,
        region=region,
        sku_id=sku,
        quantity=qty,
        unit_price=price,
        total_amount=total,
        payment_method=random.choice(["ApplePay", "Visa", "Mastercard", "Contactless"]),
        inventory_remaining_estimate=inventory_rem
    )

def main():
    parser = argparse.ArgumentParser(description="Retail POS Stream Generator")
    parser.add_argument("--rate", type=float, default=5.0, help="Transactions per sec")
    parser.add_argument("--duration", type=int, default=30, help="Duration in sec")
    parser.add_argument("--stockouts", action="store_true", help="Simulate rapid stock depletion")
    parser.add_argument("--output", choices=["console", "json"], default="console")
    args = parser.parse_args()

    interval = 1.0 / max(0.1, args.rate)
    start_time = time.time()
    count = 0

    print(f">> [Retail POS Streamer] Starting stream at {args.rate} txn/sec...")
    try:
        while True:
            is_risk = args.stockouts and (random.random() < 0.2)
            event = generate_event(simulate_stockout_risk=is_risk)
            count += 1

            if args.output == "json":
                print(event.to_json())
            else:
                alert = "[LOW INVENTORY]" if event.inventory_remaining_estimate <= 3 else "[NORMAL]       "
                print(f"{alert} Store: {event.store_id} | SKU: {event.sku_id:20} | Qty: {event.quantity} | Total: ${event.total_amount:6.2f} | Stock Left: {event.inventory_remaining_estimate:3}")

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"\n>> Stream finished. Emitted {count} POS transactions.")

if __name__ == "__main__":
    main()
