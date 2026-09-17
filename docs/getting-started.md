# 🚀 Getting Started with the watsonx.data on IBM Power Demo

---

## 1. Setting Up Your Environment

1. Ensure Python 3.9+ is installed.
2. Install generator dependencies:
   ```bash
   cd event-generators
   pip install -r requirements.txt
   ```

---

## 2. Running a Live Demo Session

### Step 1: Start the Streaming Generator
Choose the vertical that matches your client's industry:

- **Telco:** `python event-generators/telco-network-metrics.py --rate 10 --anomalies`
- **Retail:** `python event-generators/retail-pos-events.py --rate 8 --stockouts`
- **Financial Services:** `python event-generators/finance-transactions.py --rate 10 --fraud`
- **Healthcare:** `python event-generators/healthcare-patient-events.py --rate 5 --surge`

### Step 2: Showcase Open Lakehouse Federation
Open the corresponding SQL file in `queries/<vertical>/` and demonstrate how Presto aggregates real-time stream data with legacy transactional systems (Db2 for IBM i / Oracle on AIX) with **zero data movement**.

### Step 3: Close on Commercial Advantage
Double-click `power-advantage/licensing-calc.html` in your browser to calculate the exact licensing and infrastructure savings on IBM Power vs x86.
