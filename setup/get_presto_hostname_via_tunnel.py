#!/usr/bin/env python3
"""
Run this ON RHEL through the Satellite tunnel to get the real Presto engine hostname.
Traffic to localhost:31618 routes through the wxd-presto cloud endpoint into IBM Cloud,
bypassing Cloudflare entirely.
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, sys, os

WXD_APIKEY    = os.environ['WXD_APIKEY']
INSTANCE_CRN  = os.environ['WXD_INSTANCE_CRN']
INSTANCE_GUID = os.environ['WXD_INSTANCE_GUID']
# Route through the wxd-api Satellite cloud endpoint on localhost
# wxd-api (port 29998) -> eu-gb.lakehouse.cloud.ibm.com:443  (Lakehouse REST API)
# wxd-presto (port 29999) -> <engine-host>:32564              (Presto query engine)
TUNNEL_HOST   = 'localhost'
TUNNEL_PORT   = 29998   # wxd-api cloud endpoint

# Step 1 — get IAM token (iam.cloud.ibm.com is reachable directly, not Cloudflare-blocked)
data = urllib.parse.urlencode({
    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    'apikey': WXD_APIKEY
}).encode()
req = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print("IAM token obtained.")

# Step 2 — call engines API through the tunnel
# The tunnel forwards to eu-gb.lakehouse.cloud.ibm.com:443, so we construct
# the URL as if we're calling it directly but via the local port.
import http.client, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = http.client.HTTPSConnection(TUNNEL_HOST, TUNNEL_PORT, context=ctx)
conn.request('GET',
    f'/lakehouse/api/v3/{INSTANCE_GUID}/prestissimo_engines',
    headers={
        'Authorization':  'Bearer ' + token,
        'AuthInstanceId': INSTANCE_CRN,
        'Host':           'eu-gb.lakehouse.cloud.ibm.com',
    }
)
resp = conn.getresponse()
body = resp.read()
print(f"HTTP {resp.status}")

if resp.status != 200:
    print(body.decode())
    sys.exit(1)

engines = json.loads(body).get('prestissimo_engines', [])
print(f"Found {len(engines)} engine(s):")
for eng in engines:
    eid      = eng.get('engine_id', '?')
    status   = eng.get('status', '?')
    hostname = eng.get('endpoints', {}).get('hostname', '?')
    port     = eng.get('endpoints', {}).get('application_api', 31618)
    print(f"  engine_id : {eid}")
    print(f"  status    : {status}")
    print(f"  hostname  : {hostname}")
    print(f"  port      : {port}")
    print()
    if hostname and hostname != '?':
        print(f"PRESTO_HOST={hostname}")
        print(f"PRESTO_PORT={port}")
