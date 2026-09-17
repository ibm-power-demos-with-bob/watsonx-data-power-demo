import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, os

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']

# Get IAM token
data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
req = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
    headers={'Content-Type':'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print("IAM token obtained.")

# List endpoints
req2 = urllib.request.Request(
    f'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/{CONNECTOR_ID}/endpoints',
    headers={'Authorization': 'Bearer ' + token}
)
result = json.loads(urllib.request.urlopen(req2).read())
eps = result.get('endpoints', [])
print(f"Found {len(eps)} endpoints:")
for ep in eps:
    print(f"  [{ep.get('endpoint_id','')}]  {ep['display_name']:25s}  type={ep.get('connection_type','?'):8s}  dest={ep.get('server_host','?')}:{ep.get('server_port','?')}  client={ep.get('client_host','?')}:{ep.get('client_port','?')}  enabled={ep.get('enabled','?')}")
