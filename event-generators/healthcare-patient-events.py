#!/usr/bin/env python3
"""
Healthcare Patient Flow & Bed Management Event Generator
Simulates emergency admissions, transfers, and bed occupancy
to showcase real-time operational hospital analytics on IBM Power.
"""

import argparse
import random
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from shared.event_schema import HealthcarePatientEvent, current_iso_time, current_epoch_ms

FACILITIES = [f"HOSP-REGIONAL-{i:02d}" for i in range(1, 6)]
DEPARTMENTS = ["Emergency", "Cardiology", "Trauma", "Pediatrics", "ICU", "General_Ward"]

def generate_event(simulate_surge: bool = False) -> HealthcarePatientEvent:
    facility = random.choice(FACILITIES)
    dept = random.choice(DEPARTMENTS)
    
    if simulate_surge:
        acuity = random.choice([1, 2, 2, 3]) # Higher acuity
        wait_time = random.randint(95, 240)
        bed_occ = round(random.uniform(92.0, 99.8), 1)
        staff_ratio = round(random.uniform(0.55, 0.75), 2)
    else:
        acuity = random.choice([3, 4, 4, 5])
        wait_time = random.randint(10, 45)
        bed_occ = round(random.uniform(60.0, 84.0), 1)
        staff_ratio = round(random.uniform(0.95, 1.25), 2)

    return HealthcarePatientEvent(
        event_id=f"med-{uuid.uuid4().hex[:10]}",
        event_type="patient_admission",
        timestamp=current_iso_time(),
        epoch_ms=current_epoch_ms(),
        admission_id=f"ADM-{random.randint(100000, 999999)}",
        facility_id=facility,
        department=dept,
        acuity_level=acuity,
        wait_time_minutes=wait_time,
        bed_occupancy_pct=bed_occ,
        staffing_ratio=staff_ratio
    )

def main():
    parser = argparse.ArgumentParser(description="Healthcare Patient Flow Generator")
    parser.add_argument("--rate", type=float, default=4.0, help="Admissions/events per sec")
    parser.add_argument("--duration", type=int, default=30, help="Duration in sec")
    parser.add_argument("--surge", action="store_true", help="Simulate emergency surge / high bed occupancy")
    parser.add_argument("--output", choices=["console", "json"], default="console")
    args = parser.parse_args()

    interval = 1.0 / max(0.1, args.rate)
    start_time = time.time()
    count = 0

    print(f">> [Healthcare Streamer] Starting patient flow stream at {args.rate} evt/sec...")
    try:
        while True:
            is_surge = args.surge and (random.random() < 0.25)
            event = generate_event(simulate_surge=is_surge)
            count += 1

            if args.output == "json":
                print(event.to_json())
            else:
                alert = "[CAPACITY SURGE]" if event.bed_occupancy_pct >= 90.0 else "[STABLE]        "
                print(f"{alert} Facility: {event.facility_id} | Dept: {event.department:12} | Acuity: {event.acuity_level} | Wait: {event.wait_time_minutes:3}m | Bed Occ: {event.bed_occupancy_pct:4.1f}%")

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

    print(f"\n>> Stream finished. Emitted {count} patient flow events.")

if __name__ == "__main__":
    main()
