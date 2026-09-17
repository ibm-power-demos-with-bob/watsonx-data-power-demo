"""
Satellite endpoint maintenance for fresh on-prem reservation.
  1. Updates ibmi-db2 destination to new IBM i IP (129.40.125.73)
  2. Creates wxd-presto cloud endpoint pointing at Presto engine
  3. Prints a summary of all endpoints with their client host:port
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, sys, os

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']
BASE         = 'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/' + CONNECTOR_ID

# Pass as env var or edit here once retrieved via get_presto_hostname_via_tunnel.py
PRESTO_HOST  = os.environ.get('PRESTO_HOST', 'REPLACE_WITH_PRESTO_ENGINE_HOSTNAME')
PRESTO_PORT  = int(os.environ.get('PRESTO_PORT', '31618'))

NEW_IBMI_IP  = os.environ.get('SAT_IBMI_IP', '')
IBMI_PORT    = 8471

IBMI_EP_ID   = os.environ.get('SAT_IBMI_EP_ID', '')

def get_token():
    data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
    req  = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
               headers={'Content-Type':'application/x-www-form-urlencoded'})
    return json.loads(urllib.request.urlopen(req).read())['access_token']

def api(method, path, body=None, token=''):
    url  = BASE + path
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method,
               headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()) if resp.read else {}
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()}")
        raise

def list_endpoints(token):
    req = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
    return json.loads(urllib.request.urlopen(req).read()).get('endpoints', [])

if PRESTO_HOST == 'REPLACE_WITH_PRESTO_ENGINE_HOSTNAME':
    print("ERROR: Set PRESTO_HOST before running.")
    sys.exit(1)

print("Obtaining IAM token...")
token = get_token()
print("OK")

# Step 1 — patch ibmi-db2 destination IP
print(f"\nUpdating ibmi-db2 destination to {NEW_IBMI_IP}:{IBMI_PORT} ...")
patch_body = {"server_host": NEW_IBMI_IP, "server_port": IBMI_PORT}
req = urllib.request.Request(
    BASE + f'/endpoints/{IBMI_EP_ID}',
    data=json.dumps(patch_body).encode(),
    method='PATCH',
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    print(f"  OK — {resp.status}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}: {e.read().decode()}")

# Step 2 — create wxd-presto cloud endpoint
print(f"\nCreating wxd-presto cloud endpoint → {PRESTO_HOST}:{PRESTO_PORT} ...")
create_body = {
    "display_name": "wxd-presto",
    "server_host":  PRESTO_HOST,
    "server_port":  PRESTO_PORT,
    "server_protocol": "tcp",
    "client_protocol": "tcp",
    "connection_type": "cloud"
}
req2 = urllib.request.Request(
    BASE + '/endpoints',
    data=json.dumps(create_body).encode(),
    method='POST',
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
)
try:
    resp2 = urllib.request.urlopen(req2)
    ep = json.loads(resp2.read())
    print(f"  Created: id={ep.get('endpoint_id')}  client_port={ep.get('client_port')}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}: {e.read().decode()}")

# Final summary
print("\n--- All endpoints ---")
for ep in list_endpoints(token):
    print(f"  {ep['display_name']:25s}  dest={ep.get('server_host','?')}:{ep.get('server_port','?')}  client=...:{ep.get('client_port','?')}")
