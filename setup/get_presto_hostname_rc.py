"""
Retrieves the Presto engine hostname via the IBM Cloud Resource Controller API.
This endpoint is NOT behind Cloudflare, so it works from outside IBM Cloud.
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, os

WXD_APIKEY    = os.environ['WXD_APIKEY']
INSTANCE_GUID = os.environ['WXD_INSTANCE_GUID']

# Get IAM token
data = urllib.parse.urlencode({
    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    'apikey': WXD_APIKEY
}).encode()
req = urllib.request.Request('https://iam.cloud.ibm.com/identity/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print("IAM token obtained.")

# Try the global search API to find the instance and its dashboard URL
# (the dashboard URL often contains the hostname)
req2 = urllib.request.Request(
    f'https://resource-controller.cloud.ibm.com/v2/resource_instances/{INSTANCE_GUID}',
    headers={'Authorization': 'Bearer ' + token}
)
result = json.loads(urllib.request.urlopen(req2).read())
print(f"\nInstance name   : {result.get('name')}")
print(f"State           : {result.get('state')}")
print(f"Dashboard URL   : {result.get('dashboard_url','not present')}")
print(f"Resource plan   : {result.get('resource_plan_id','?')}")
# Print all keys so we can see what's available
print("\nAll top-level keys:")
for k, v in result.items():
    if k not in ('extensions', 'parameters'):
        print(f"  {k}: {v}")
print(f"\nextensions: {json.dumps(result.get('extensions', {}), indent=2)}")
