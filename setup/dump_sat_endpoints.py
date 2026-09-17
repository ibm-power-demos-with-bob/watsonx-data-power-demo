import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, os

APIKEY       = os.environ['SAT_APIKEY']
CONNECTOR_ID = os.environ['SAT_CONNECTOR_ID']
BASE         = 'https://api.eu-gb.link.satellite.cloud.ibm.com/v1/connectors/' + CONNECTOR_ID

data = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':APIKEY}).encode()
req  = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
           headers={'Content-Type':'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']

req2 = urllib.request.Request(BASE+'/endpoints', headers={'Authorization':'Bearer '+token})
eps  = json.loads(urllib.request.urlopen(req2).read()).get('endpoints', [])
for ep in eps:
    print(json.dumps(ep, indent=2))
    print()
