"""Create wxd-api cloud endpoint pointing at eu-gb.lakehouse.cloud.ibm.com:443
for Lakehouse REST API calls from RHEL through the Satellite tunnel."""
import _config  # noqa: F401
import urllib.request, urllib.parse, json, os, sys

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']
BASE         = 'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/' + CONNECTOR_ID

data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
req  = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
           headers={'Content-Type':'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print('IAM token: OK')

# Create wxd-api cloud endpoint
body = json.dumps({
    'display_name':    'wxd-api',
    'server_host':     'eu-gb.lakehouse.cloud.ibm.com',
    'server_port':     443,
    'server_protocol': 'tcp',
    'client_protocol': 'tcp',
    'conn_type':       'cloud'
}).encode()
req2 = urllib.request.Request(BASE+'/endpoints', data=body, method='POST',
           headers={'Authorization':'Bearer '+token, 'Content-Type':'application/json'})
try:
    resp = urllib.request.urlopen(req2)
    ep   = json.loads(resp.read())
    print(f"Created wxd-api: endpoint_id={ep.get('endpoint_id')}  client_port={ep.get('client_port')}")
except urllib.error.HTTPError as e:
    body_err = e.read().decode()
    print(f'HTTP {e.code}: {body_err}')
    if 'already exists' in body_err:
        print('Endpoint already exists — listing current ports:')

# Summary
req3 = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
for e in json.loads(urllib.request.urlopen(req3).read()).get('endpoints', []):
    print(f"  {e['display_name']:25s}  dest={e.get('server_host','?')}:{e.get('server_port','?')}  client_port={e.get('client_port','?')}")
