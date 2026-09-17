"""Temporary script — patch wxd-presto endpoint to real Presto hostname."""
import _config  # noqa: F401
import urllib.request, urllib.parse, json, os, sys

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']
BASE         = 'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/' + CONNECTOR_ID

PRESTO_HOST  = 'ff5b1b42-0d0a-4d03-ac39-b4529cbda74c.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud'
PRESTO_PORT  = 32564

data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
req  = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
           headers={'Content-Type':'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print('IAM token: OK')

req2 = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
eps  = json.loads(urllib.request.urlopen(req2).read()).get('endpoints', [])
ep   = next((e for e in eps if e['display_name'] == 'wxd-presto'), None)
if not ep:
    print('ERROR: wxd-presto not found'); sys.exit(1)
ep_id = ep['endpoint_id']
print(f'wxd-presto endpoint_id: {ep_id}')

patch = json.dumps({'server_host': PRESTO_HOST, 'server_port': PRESTO_PORT}).encode()
req3  = urllib.request.Request(BASE+f'/endpoints/{ep_id}', data=patch, method='PATCH',
            headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
try:
    resp = urllib.request.urlopen(req3)
    print(f'PATCH -> HTTP {resp.status}  OK')
except urllib.error.HTTPError as e:
    print(f'PATCH -> HTTP {e.code}: {e.read().decode()}')

req4 = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
for e in json.loads(urllib.request.urlopen(req4).read()).get('endpoints', []):
    print(f"  {e['display_name']:25s}  dest={e.get('server_host','?')}:{e.get('server_port','?')}  client_port={e.get('client_port','?')}")
