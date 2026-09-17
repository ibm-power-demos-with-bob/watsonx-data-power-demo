"""
Bootstrap step: creates the wxd-presto cloud endpoint with a temporary destination
(eu-gb.lakehouse.cloud.ibm.com:443) so the agent can start and we can call the
Lakehouse API through the tunnel to discover the real Presto engine hostname.

After running this:
  1. Note the assigned client_port printed below
  2. Start the Satellite agent on RHEL (setup/start_satellite_agent.sh)
  3. Run setup/get_presto_hostname_via_tunnel.py from RHEL to get the real hostname
  4. Run setup/update_sat_endpoints.py to patch wxd-presto to the real hostname:31618

Credentials are read from setup/config.env (gitignored).
Copy setup/config.env.template -> setup/config.env and fill in before running.
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, os

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']
BASE         = 'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/' + CONNECTOR_ID

IBMI_EP_ID   = os.environ.get('SAT_IBMI_EP_ID', '')
NEW_IBMI_IP  = os.environ.get('SAT_IBMI_IP', '')

def get_token():
    data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
    req  = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
               headers={'Content-Type':'application/x-www-form-urlencoded'})
    return json.loads(urllib.request.urlopen(req).read())['access_token']

def sat_request(method, path, body=None, token=''):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(BASE + path, data=data, method=method,
               headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
    try:
        resp = urllib.request.urlopen(req)
        raw  = resp.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f"  HTTP {e.code}: {msg}")
        raise

print("Obtaining IAM token...")
token = get_token()
print("OK\n")

# Step 1 — update ibmi-db2 to new IBM i IP
print(f"Updating ibmi-db2 -> {NEW_IBMI_IP}:8471 ...")
try:
    sat_request('PATCH', f'/endpoints/{IBMI_EP_ID}',
                {'server_host': NEW_IBMI_IP, 'server_port': 8471}, token)
    print("  OK")
except:
    print("  FAILED — check above error")

# Step 2 — create wxd-presto with placeholder destination
# Temporary target is the watsonx.data API hostname — we update it to the real
# Presto engine hostname after we retrieve it through the tunnel.
print("\nCreating wxd-presto cloud endpoint (placeholder destination)...")
try:
    ep = sat_request('POST', '/endpoints', {
        "display_name":    "wxd-presto",
        "server_host":     "eu-gb.lakehouse.cloud.ibm.com",
        "server_port":     443,
        "server_protocol": "tcp",
        "client_protocol": "tcp",
        "conn_type":       "cloud"
    }, token)
    client_port = ep.get('client_port', '?')
    ep_id       = ep.get('endpoint_id', '?')
    print(f"  Created: endpoint_id={ep_id}")
    print(f"  Assigned client_port: {client_port}")
    print(f"\n  *** Record this port — used in podman run -p 31618:{client_port} ***")
except Exception:
    print("  FAILED — endpoint may already exist, check below")

# Final summary
print("\n--- All endpoints ---")
req = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
for ep in json.loads(urllib.request.urlopen(req).read()).get('endpoints', []):
    print(f"  {ep['display_name']:25s}  dest={ep.get('server_host','?')}:{ep.get('server_port','?')}  client_port={ep.get('client_port','?')}")
