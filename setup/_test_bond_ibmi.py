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

def q(label, sql):
    t = time.time()
    try:
        cur.execute(sql); r = cur.fetchall()
        print(f"[OK  {time.time()-t:5.1f}s] {label}: {r[:3]}")
    except Exception as e:
        print(f"[ERR] {label}: {str(e)[:300]}")

q("columns", "SHOW COLUMNS FROM ibmi_olist.olist.bond_career_analysis")
q("count", 'SELECT count(actress_name) FROM ibmi_olist.olist.bond_career_analysis')
q("grace/denise", "SELECT actress_name, post_bond_credits_lifetime, post_bond_active_years, career_trajectory FROM ibmi_olist.olist.bond_career_analysis WHERE actress_name IN ('Grace Jones','Denise Richards')")
q("accents", "SELECT actress_name FROM ibmi_olist.olist.bond_career_analysis WHERE film_title IN ('Spectre','Skyfall')")
q("act2 style", "SELECT bond_era, COUNT(DISTINCT actress_name), ROUND(AVG(post_bond_active_years),1) FROM ibmi_olist.olist.bond_career_analysis GROUP BY bond_era")
q("act4 style", "SELECT CASE WHEN character_depth_score >= 8 THEN 'High' ELSE 'Other' END t, COUNT(*) FROM ibmi_olist.olist.bond_career_analysis GROUP BY 1")
q("act3 cross-source", "SELECT count(*) FROM ibmi_olist.olist.bond_career_analysis b JOIN pg_olist.public.industry_decade_benchmarks ind ON ind.decade = CONCAT(CAST((b.release_year / 10) * 10 AS VARCHAR), 's')")
q("act6 cross-source", """SELECT count(*) FROM ibmi_olist.olist.bond_career_analysis b
JOIN pg_olist.public.industry_decade_benchmarks ind ON ind.decade = CONCAT(CAST((b.release_year / 10) * 10 AS VARCHAR), 's')
LEFT JOIN pg_olist.public.bond_semantic_reviews v ON v.actress_name = b.actress_name AND v.film_title = b.film_title""")
