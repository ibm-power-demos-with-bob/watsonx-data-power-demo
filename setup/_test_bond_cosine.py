import sys, os, time, prestodb, urllib3
urllib3.disable_warnings()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r
conn = prestodb.dbapi.connect(
    host=_r.WXD_HOST, port=_r.WXD_PRESTO_PORT, user=_r.WXD_API_USER,
    catalog="system", schema="runtime", http_scheme="https",
    auth=prestodb.auth.BasicAuthentication(_r.WXD_API_USER, _r.WXD_API_PASS))
conn._http_session.verify = False
cur = conn.cursor()

SQL = """
WITH q AS (
  SELECT CAST(json_parse(CAST(embedding AS VARCHAR)) AS ARRAY(DOUBLE)) AS qv
  FROM pg_olist.public.bond_semantic_queries WHERE query_id = 'Q1'
),
d AS (
  SELECT doc_id, actress_name, film_year,
         CAST(json_parse(CAST(embedding AS VARCHAR)) AS ARRAY(DOUBLE)) AS dv
  FROM pg_olist.public.bond_semantic_reviews
)
SELECT d.doc_id, d.actress_name,
       reduce(zip_with(d.dv, q.qv, (a, b) -> a * b), CAST(0 AS DOUBLE), (s, x) -> s + x, s -> s) AS cosine
FROM d CROSS JOIN q
ORDER BY cosine DESC LIMIT 5
"""
t = time.time()
cur.execute(SQL)
for r in cur.fetchall():
    print(r)
print(f"{time.time()-t:.1f}s")
