import sys, os, prestodb, urllib3
urllib3.disable_warnings()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r
conn = prestodb.dbapi.connect(
    host=_r.WXD_HOST, port=_r.WXD_PRESTO_PORT,
    user=_r.WXD_API_USER, catalog="system", schema="runtime",
    http_scheme="https",
    auth=prestodb.auth.BasicAuthentication(_r.WXD_API_USER, _r.WXD_API_PASS)
)
conn._http_session.verify = False
cur = conn.cursor()

# Core federated join: PostgreSQL suppliers + IBM i order items
q = (
    'SELECT s.supplier_id, s.state, s.region_label, '
    'oi."order id", oi.price '
    'FROM pg_olist.olist.v_suppliers s '
    'JOIN ibmi_olist.olist.v_orderitems oi '
    'ON s.supplier_id = oi."seller id" '
    'LIMIT 5'
)
cur.execute(q)
rows = cur.fetchall()
print("Cross-catalog join rows:", len(rows))
for r in rows:
    print(" ", r)

# Full 3-way join: pg suppliers + ibmi orderitems + ibmi orders
q2 = (
    'SELECT s.supplier_id, s.region_label, '
    'o."order status", o."purchase timestamp" '
    'FROM pg_olist.olist.v_suppliers s '
    'JOIN ibmi_olist.olist.v_orderitems oi ON s.supplier_id = oi."seller id" '
    'JOIN ibmi_olist.olist.v_orders o ON oi."order id" = o."order id" '
    'WHERE o."order status" = \'delivered\' '
    'LIMIT 5'
)
cur.execute(q2)
rows2 = cur.fetchall()
print("\n3-way join (delivered orders):", len(rows2))
for r in rows2:
    print(" ", r)
