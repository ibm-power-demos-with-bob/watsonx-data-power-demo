import paramiko, sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST, SSH_USER, SSH_KEY
try:
    k = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
except Exception:
    k = paramiko.RSAKey.from_private_key_file(SSH_KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=k)
_, o, _ = c.exec_command('grep BOND ~/demo-ui/.env.local')
print("env:", o.read().decode().strip())
for act in range(1, 7):
    t = time.time()
    _, o, _ = c.exec_command(f'curl -s "http://localhost:3000/api/bond-query?act={act}"')
    raw = o.read().decode()
    try:
        j = json.loads(raw)
    except Exception:
        print(f"Act {act}: ERROR {raw[:300]}"); continue
    sql = j["sql"]
    src = "ibmi_olist" if "ibmi_olist" in sql else ("pg_olist" if "pg_olist" in sql else "?")
    cats = [(x["name"], x["engine"]) for x in j["catalogsQueried"]]
    print(f"Act {act}: OK {time.time()-t:4.1f}s rows={len(j['rows'])} sql-career-src={src} catalogs={cats}")
    if act == 6:
        for r in j["rows"]:
            if r["actress_name"] in ("Grace Jones", "Denise Richards"):
                print("   ", r["actress_name"], r["post_bond_credits"], r["post_active_years"], r["career_trajectory"])
c.close()
