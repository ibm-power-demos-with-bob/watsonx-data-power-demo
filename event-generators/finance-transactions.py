#!/usr/bin/env python3
"""
Financial Services Transaction Event Generator
Simulates card and digital payment transactions to demonstrate real-time fraud scoring
and federation with core core banking systems (Db2 on IBM i).
"""

import argparse
import random
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from shared.event_schema import FinanceTransactionEvent, current_iso_time, current_epoch_ms

MERCHANTS = [f"MCH-{i:04d}" for i in range(100, 300)]
COUNTRIES = ["GB", "FR", "DE", "US", "CH", "ES", "SG", "JP"]

def generate_event(inject_fraud: bool = False) -> FinanceTransactionEvent:
    account = f"ACC-{random.randint(100000, 999999)}"
    merchant = random.choice(MERCHANTS)
    country = random.choice(COUNTRIES)
    channel = random.choice(["E-Commerce", "Contactless_POS", "ATM_Withdrawal", "Wire_Transfer"])

    if inject_fraud:
        amount = round(random.uniform(1200.0, 9800.0), 2)
        risk = round(random.uniform(0.82, 0.99), 2)
        flagged = True
    else:
        amount = round(random.uniform(4.50, 450.0), 2)
        risk = round(random.uniform(0.01, 0.35), 2)
        flagged = False

    return FinanceTransactionEvent(
        event_id=f"tx-{uuid.uuid4().hex[:10]}",
        event_type="financial_transaction",
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        transaction_id=f"TXN-{random.randint(10000000, 99999999)}",
        account_id=account,
        merchant_id=merchant,
        amount=amount,
        currency=random.choice(["EUR", "GBP", "USD"]),
        channel=channel,
        country_code=country,
        risk_score=risk,
        is_flagged=flagged
    )

def main():
    parser = argparse.ArgumentParser(description="Financial Transaction Stream Generator")
    parser.add_argument("--rate", type=float, default=5.0, help="Transactions per sec")
    parser.add_argument("--duration", type=int, default=30, help="Duration in sec")
    parser.add_argument("--fraud", action="store_true", help="Inject high-risk fraud patterns")
    parser.add_argument("--output", choices=["console", "json"], default="console")
    args = parser.parse_args()

    interval = 1.0 / max(0.1, args.rate)
    start_time = time.time()
    count = 0

    print(f">> [Financial Streamer] Starting transaction stream at {args.rate} txn/sec...")
    try:
        while True:
            is_fraud = args.fraud and (random.random() < 0.15)
            event = generate_event(inject_fraud=is_fraud)
            count += 1

            if args.output == "json":
                print(event.to_json())
            else:
                prefix = "[FRAUD ALERT] " if event.is_flagged else "[CLEARED]     "
                print(f"{prefix} Acc: {event.account_id} | Amt: {event.currency} {event.amount:7.2f} | Risk: {event.risk_score:0.2f} | Chn: {event.channel:14} | Country: {event.country_code}")

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"\n>> Stream finished. Emitted {count} financial transactions.")

if __name__ == "__main__":
    main()
