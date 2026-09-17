"""
Checks the current state of the watsonx.data instance via the Resource Controller
and attempts to list engines/catalogs via the Lakehouse API through the
wxd-presto Satellite cloud endpoint tunnel (port 29999 on RHEL).

Run this from RHEL:  python3 /tmp/check_wxd_state.py
Run this locally:    python setup/check_wxd_state.py  (will 403 on Lakehouse calls)
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, http.client, ssl, sys, os

WXD_APIKEY    = os.environ['WXD_APIKEY']
INSTANCE_CRN  = os.environ['WXD_INSTANCE_CRN']
INSTANCE_GUID = os.environ['WXD_INSTANCE_GUID']

# When running on RHEL through tunnel, use localhost:29999
# When running locally, this will 403 — but we still get the IAM check
TUNNEL_HOST = 'localhost'
TUNNEL_PORT = 29999

# --- IAM token ---
data = urllib.parse.urlencode({
    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    'apikey': WXD_APIKEY
}).encode()
req = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print("IAM token: OK")

# --- Resource Controller: instance state (works from laptop, not Cloudflare blocked) ---
req2 = urllib.request.Request(
    f'https://resource-controller.cloud.ibm.com/v2/resource_instances/{INSTANCE_GUID}',
    headers={'Authorization': 'Bearer ' + token}
)
rc = json.loads(urllib.request.urlopen(req2).read())
print(f"Instance state : {rc.get('state')}")
print(f"Instance name  : {rc.get('name')}")
print(f"Last operation : {rc.get('last_operation', {}).get('type')} / {rc.get('last_operation', {}).get('state')}")

# --- Lakehouse API via tunnel (only works from RHEL) ---
print(f"\nCalling Lakehouse API via tunnel {TUNNEL_HOST}:{TUNNEL_PORT} ...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def lh_get(path):
    conn = http.client.HTTPSConnection(TUNNEL_HOST, TUNNEL_PORT, context=ctx, timeout=15)
    conn.request('GET', path, headers={
        'Authorization':  'Bearer ' + token,
        'AuthInstanceId': INSTANCE_CRN,
        'Host':           'eu-gb.lakehouse.cloud.ibm.com',
    })
    resp = conn.getresponse()
    body = resp.read()
    return resp.status, body

status, body = lh_get(f'/lakehouse/api/v3/{INSTANCE_GUID}/prestissimo_engines')
print(f"  GET /prestissimo_engines  -> HTTP {status}")
if status == 200:
    engines = json.loads(body).get('prestissimo_engines', [])
    for e in engines:
        print(f"    engine={e.get('engine_id')}  status={e.get('status')}  host={e.get('endpoints',{}).get('hostname','?')}")
else:
    print(f"  {body.decode()[:200]}")

status2, body2 = lh_get(f'/lakehouse/api/v3/catalogs')
print(f"  GET /catalogs             -> HTTP {status2}")
if status2 == 200:
    cats = json.loads(body2).get('catalogs', [])
    for c in cats:
        print(f"    catalog={c.get('catalog_name')}  type={c.get('catalog_type')}")
else:
    print(f"  {body2.decode()[:200]}")
