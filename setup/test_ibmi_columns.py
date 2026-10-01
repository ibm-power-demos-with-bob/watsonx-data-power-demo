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

# What columns does Presto see for v_customers?
try:
    cur.execute("SHOW COLUMNS FROM ibmi_olist.olist.v_customers")
    print("v_customers columns:", cur.fetchall())
except Exception as e:
    print("SHOW COLUMNS v_customers:", e)

# Try the base table  
try:
    cur.execute("SHOW COLUMNS FROM ibmi_olist.olist.customers")
    print("customers columns:", cur.fetchall())
except Exception as e:
    print("SHOW COLUMNS customers:", e)

# Try SELECT * with LIMIT from base table
try:
    cur.execute("SELECT * FROM ibmi_olist.olist.customers LIMIT 1")
    print("customers row:", cur.fetchall())
    print("customers desc:", cur.description)
except Exception as e:
    print("SELECT customers:", e)

# Try SELECT * from view
try:
    cur.execute("SELECT * FROM ibmi_olist.olist.v_customers LIMIT 1")
    print("v_customers row:", cur.fetchall())
    print("v_customers desc:", cur.description)
except Exception as e:
    print("SELECT v_customers:", e)
