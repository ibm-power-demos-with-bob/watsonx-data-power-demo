"""
Shared event schema definitions and helper serialization utilities.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Any, Dict

def current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()

def current_epoch_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)

@dataclass
class BaseEvent:
    event_id: str
    event_type: str
    timestamp: str
    epoch_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

@dataclass
class TelcoMetricEvent(BaseEvent):
    tower_id: str
    region: str
    signal_strength_dbm: float
    latency_ms: int
    packet_loss_pct: float
    active_users: int
    cpu_util_pct: float
    status: str

@dataclass
class RetailPosEvent(BaseEvent):
    transaction_id: str
    store_id: str
    region: str
    sku_id: str
    quantity: int
    unit_price: float
    total_amount: float
    payment_method: str
    inventory_remaining_estimate: int

@dataclass
class FinanceTransactionEvent(BaseEvent):
    transaction_id: str
    account_id: str
    merchant_id: str
    amount: float
    currency: str
    channel: str # POS, Online, ATM
    country_code: str
    risk_score: float
    is_flagged: bool

@dataclass
class HealthcarePatientEvent(BaseEvent):
    admission_id: str
    facility_id: str
    department: str
    acuity_level: int # 1 (Critical) to 5 (Non-urgent)
    wait_time_minutes: int
    bed_occupancy_pct: float
    staffing_ratio: float

@dataclass
class ExternalSignalEvent(BaseEvent):
    """
    A structured external market / environmental signal injected into the
    Iceberg event stream.  Can originate from a live API (news, weather,
    stock price) or be synthetically injected via signal-injector.py for
    demo purposes.  The AI sidecar watches for these alongside POS events
    and fires the federated alert query when severity is HIGH or CRITICAL.

    signal_category : MARKET_EVENT | WEATHER_EVENT | LOGISTICS_DISRUPTION
    signal_code     : short machine-readable code (e.g. IBM_PROFIT_WARNING,
                      EU_HEATWAVE_2025, PORT_CLOSURE_ROTTERDAM)
    affected_sector : sector tag matching OLIST.PRODUCTS.SECTOR — the
                      sidecar uses this to scope the federated alert query
    severity        : LOW | MEDIUM | HIGH | CRITICAL
    headline        : human-readable summary shown on the dashboard card
    detail_url      : optional reference URL (FT article, NASA page, etc.)
    temp_celsius    : populated for WEATHER_EVENT signals (peak temperature)
    ticker_symbol   : populated for MARKET_EVENT signals (e.g. IBM)
    price_change_pct: populated for MARKET_EVENT signals (e.g. -25.0)
    injected        : True when synthetically injected (not from live API)
    """
    signal_category: str
    signal_code: str
    affected_sector: str
    severity: str
    headline: str
    detail_url: str
    temp_celsius: float | None
    ticker_symbol: str | None
    price_change_pct: float | None
    injected: bool
    source_feed: str | None = None
    source_channel: str | None = None
