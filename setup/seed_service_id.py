"""
Make an authenticated call to the watsonx.data API using the service ID key.
This registers the service ID in watsonx.data's MetaStore so it becomes
searchable in the Access Control "Grant access" dialog.
"""
import _config  # noqa: F401 — loads setup/config.env into os.environ
import urllib.request, urllib.parse, json, base64, sys, os

APIKEY = os.environ['WXD_APIKEY']
CRN    = os.environ['WXD_INSTANCE_CRN']
GUID   = os.environ['WXD_INSTANCE_GUID']
HOST   = "eu-gb.lakehouse.cloud.ibm.com"

# 1. Get IAM token
print("Exchanging API key for IAM token...")
data = urllib.parse.urlencode({
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": APIKEY
}).encode()
req = urllib.request.Request(
    "https://iam.cloud.ibm.com/identity/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
print("  Got token OK")

# Decode to confirm identity
p = token.split(".")[1]
p += "=" * (4 - len(p) % 4)
claims = json.loads(base64.b64decode(p))
print(f"  Identity: {claims.get('name')} ({claims.get('sub_type')})")
print(f"  IAM ID:   {claims.get('iam_id')}")

# 2. Call the watsonx.data catalogs endpoint to seed the service ID into MDS
print("\nCalling watsonx.data API to seed service ID into MetaStore...")
url = f"https://{HOST}/lakehouse/api/v3/{GUID}/catalogs"
req2 = urllib.request.Request(
    url,
    headers={
        "Authorization": "Bearer " + token,
        "AuthInstanceId": CRN,
        "Content-Type": "application/json"
    }
)
try:
    resp = json.loads(urllib.request.urlopen(req2).read())
    catalogs = [c.get("catalog_name") for c in resp.get("catalogs", [])]
    print(f"  Catalogs visible: {catalogs}")
    print("\nSUCCESS: Service ID has now made an authenticated call to this instance.")
    print("Now go to watsonx.data Access Control -> pg_olist -> Grant access")
    print("and search for 'wxd-demo-query' - it should now appear.")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"  HTTP {e.code}: {body}")
    if e.code == 403:
        print("\n  403: service ID still has no IAM policy on this instance.")
        print("  Make sure wxd-demo-query is in the itz-110000sg2k-limql82k access group.")
