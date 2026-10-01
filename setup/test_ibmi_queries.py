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

# SHOW SCHEMAS
try:
    cur.execute("SHOW SCHEMAS IN ibmi_olist")
    print("SCHEMAS:", cur.fetchall())
except Exception as e:
    print("SHOW SCHEMAS ERROR:", e)

# Simple SELECT 1
try:
    cur.execute("SELECT 1 FROM ibmi_olist.olist.customers LIMIT 1")
    print("SELECT 1 from customers:", cur.fetchall())
except Exception as e:
    print("SELECT 1 ERROR:", e)

# Try SHOW TABLES
try:
    cur.execute("SHOW TABLES IN ibmi_olist.olist")
    print("TABLES:", cur.fetchall())
except Exception as e:
    print("SHOW TABLES ERROR:", e)

# Try selecting an actual column rather than count(*)
try:
    cur.execute("SELECT customer_id FROM ibmi_olist.olist.v_customers LIMIT 3")
    print("v_customers sample:", cur.fetchall())
except Exception as e:
    print("v_customers ERROR:", e)
