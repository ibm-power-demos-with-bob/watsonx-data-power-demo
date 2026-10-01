import prestodb
import urllib3

urllib3.disable_warnings()

conn = prestodb.dbapi.connect(
    host="eu-de.services.cloud.techzone.ibm.com",
    port=25820,
    user="ibmlhadmin",
    catalog="system",
    schema="runtime",
    http_scheme="https",
    auth=prestodb.auth.BasicAuthentication("ibmlhadmin", "password")
)
conn._http_session.verify = False
cur = conn.cursor()

# The actual demo query from the UI — cross-catalog join
demo_query = """
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    c."customer id"     AS customer_id,
    c.city              AS customer_city,
    o."order id"        AS order_id
FROM pg_olist.olist.v_suppliers s
JOIN ibmi_olist.olist.v_orders o
  ON s.seller_state = o.state
JOIN ibmi_olist.olist.v_customers c
  ON o."customer id" = c."customer id"
LIMIT 5
"""

try:
    cur.execute(demo_query)
    rows = cur.fetchall()
    print(f"Cross-catalog join: {len(rows)} rows")
    for r in rows:
        print(" ", r)
except Exception as e:
    print("Demo query ERROR:", e)

# Also check the detect-signals query pattern
detect_query = """
SELECT s.supplier_name, s.risk_tier, c."customer id", c.city
FROM pg_olist.olist.v_suppliers s
CROSS JOIN ibmi_olist.olist.v_customers c
LIMIT 3
"""
try:
    cur.execute(detect_query)
    rows = cur.fetchall()
    print(f"\nDetect-signals pattern: {len(rows)} rows")
    for r in rows[:3]:
        print(" ", r)
except Exception as e:
    print("Detect query ERROR:", e)
