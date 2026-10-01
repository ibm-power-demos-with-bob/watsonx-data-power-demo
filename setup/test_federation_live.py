import sys, os, time
import prestodb
import urllib3

urllib3.disable_warnings()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r

conn = prestodb.dbapi.connect(
    host=_r.WXD_HOST,
    port=_r.WXD_PRESTO_PORT,
    user=_r.WXD_API_USER,
    catalog="system",
    schema="runtime",
    http_scheme="https",
    auth=prestodb.auth.BasicAuthentication(_r.WXD_API_USER, _r.WXD_API_PASS)
)
conn._http_session.verify = False
cur = conn.cursor()
cur.execute("SHOW CATALOGS")
print("SHOW CATALOGS:", cur.fetchall())

try:
    cur.execute("SELECT count(*) FROM pg_olist.olist.v_suppliers")
    print("PG v_suppliers COUNT:", cur.fetchall())
except Exception as e:
    print("PG ERROR:", e)

try:
    # NOTE: COUNT(*) fails on IBM i via Presto JDBC — must name a column
    cur.execute('SELECT count("customer id") FROM ibmi_olist.olist.v_customers')
    print("IBMi v_customers COUNT:", cur.fetchall())
except Exception as e:
    print("IBMi ERROR:", e)
