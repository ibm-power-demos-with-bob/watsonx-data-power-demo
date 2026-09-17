"""
Retrieves the Presto engine hostname from the watsonx.data REST API.
Uses the TechZone service API key — no GUI or browser session needed.
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, os

WXD_APIKEY    = os.environ['WXD_APIKEY']
INSTANCE_CRN  = os.environ['WXD_INSTANCE_CRN']
INSTANCE_GUID = os.environ['WXD_INSTANCE_GUID']
WXD_API_BASE  = 'https://eu-gb.lakehouse.cloud.ibm.com'

# Get IAM token
data = urllib.parse.urlencode({
    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    'apikey': WXD_APIKEY
}).encode()
req = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print("IAM token obtained.")

# Query prestissimo engines
req2 = urllib.request.Request(
    f'{WXD_API_BASE}/lakehouse/api/v3/{INSTANCE_GUID}/prestissimo_engines',
    headers={
        'Authorization':  'Bearer ' + token,
        'AuthInstanceId': INSTANCE_CRN,
    }
)
result = json.loads(urllib.request.urlopen(req2).read())
engines = result.get('prestissimo_engines', [])
print(f"\nFound {len(engines)} Presto engine(s):")
for eng in engines:
    name     = eng.get('engine_id', eng.get('display_name', '?'))
    status   = eng.get('status', '?')
    hostname = eng.get('endpoints', {}).get('hostname', '?')
    port     = eng.get('endpoints', {}).get('application_api', '?')
    print(f"  engine_id : {name}")
    print(f"  status    : {status}")
    print(f"  hostname  : {hostname}")
    print(f"  port      : {port}")
    print()
