# 📊 Checkpoint Topic — Data Model & Dataset Options

_Referenced from `_checkpoint.md`. Content for per-vertical dataset selection only._

## Design Principle
The demo is **industry-tailorable**. The three-layer architecture stays constant across verticals — only the tables and datasets swap. IBM i always plays the "core ERP / system of record" role; EDB always plays the "operational DB" role; Iceberg always plays the "live event stream" role. The federated query pattern is identical regardless of industry.

## Recommended Datasets by Vertical

### 🛒 Retail (Primary / Default Vertical)
| Layer | Dataset | Source | Tables |
|---|---|---|---|
| **IBM i** | Olist Brazilian E-Commerce | [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — public CSV, no licence friction | `ORDERS`, `ORDER_ITEMS`, `CUSTOMERS`, `PRODUCTS` |
| **EDB** | Olist (supplier/seller subset) | Same download | `SUPPLIERS`, `PURCHASE_ORDERS`, `WAREHOUSES` |
| **Iceberg** | Synthetic POS events | Our `retail-pos-events.py` generator, seeded with Olist SKUs | `retail_pos_events`, `inventory_events` |
| **Why Olist on IBM i** | Real commercial data, 100k orders, 32k products, clean relational schema — exactly what an IBM i retail ERP holds | | |

### 💳 Financial Services
| Layer | Dataset | Source | Tables |
|---|---|---|---|
| **IBM i** | PaySim account/customer master (subset) | [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1) — synthetic, Apache-style licence | `ACCOUNTS`, `CUSTOMERS`, `MERCHANTS` |
| **EDB** | PaySim counterparty / merchant data | Same download | `MERCHANTS`, `COUNTERPARTIES` |
| **Iceberg** | PaySim transactions replayed as live stream | `finance-transactions.py` generator seeded with PaySim IDs | `finance_transactions`, `fraud_flags` |
| **Why PaySim** | 6M synthetic transactions with realistic fraud patterns, clean flat schema, safe to use in demos | | |

### 🏥 Healthcare
| Layer | Dataset | Source | Tables |
|---|---|---|---|
| **IBM i** | Synthea synthetic patient records | [GitHub](https://github.com/synthetichealth/synthea) — Apache 2.0, generates CSV/FHIR | `PATIENTS`, `ENCOUNTERS`, `CONDITIONS`, `MEDICATIONS` |
| **EDB** | Synthea providers / facilities | Same generation run | `PROVIDERS`, `FACILITIES`, `CARE_TEAMS` |
| **Iceberg** | Live admission/discharge/bed events | `healthcare-patient-events.py` seeded with Synthea patient IDs | `healthcare_patient_events`, `bed_availability` |
| **Why Synthea** | Used by NHS Digital and US health systems for testing; configurable volumes; clinically realistic | | |

### 📡 Telco
| Layer | Dataset | Source | Tables |
|---|---|---|---|
| **IBM i** | Synthetic customer/subscriber master | Generated — no external dataset needed | `SUBSCRIBERS`, `CONTRACTS`, `BILLING_ACCOUNTS` |
| **EDB** | Synthetic network asset register | Generated | `TOWERS`, `CELLS`, `NETWORK_SEGMENTS` |
| **Iceberg** | Live tower KPI / anomaly events | `telco-network-metrics.py` (already well-structured, no external seed needed) | `telco_network_metrics`, `anomaly_events` |
| **Why synthetic** | The 5G dataset from UCC/MISL is too raw (measurement logs, not operational schema). Our existing generator already produces the right tower/region/KPI structure. |  | |

## Datasets Evaluated but Not Recommended
| Dataset | Reason not selected |
|---|---|
| [Instacart Basket Prediction](https://github.com/sjvasquez/instacart-basket-prediction) | ML wrapper — use raw Instacart Kaggle data if needed; Olist is cleaner for our purposes |
| [M5 Forecasting (Walmart)](https://www.kaggle.com/competitions/m5-forecasting-accuracy) | Wide time-series matrix format, not relational ERP schema; better for Spark/ML demo |
| [5G Dataset (UCC MISL)](https://github.com/uccmisl/5Gdataset) | Raw RF measurements, not operational telemetry; synthetic generator is more demo-appropriate |
