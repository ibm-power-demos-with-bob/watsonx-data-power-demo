import urllib.request, urllib.parse, json, base64, sys

apikey = sys.argv[1] if len(sys.argv) > 1 else "cCJ82TpKwibZubhEgq7dHcPgsU96kEBOfs3G53DKC2I1"

data = urllib.parse.urlencode({
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": apikey
}).encode()

req = urllib.request.Request(
    "https://iam.cloud.ibm.com/identity/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
resp = json.loads(urllib.request.urlopen(req).read())
token = resp["access_token"]

p = token.split(".")[1]
p += "=" * (4 - len(p) % 4)
claims = json.loads(base64.b64decode(p))

print("=== Token identity ===")
for k in ["sub", "iam_id", "sub_type", "name", "email", "iss"]:
    if k in claims:
        print(f"  {k}: {claims[k]}")

print("\n=== Account ===")
acct = claims.get("account", {})
print(f"  account id: {acct.get('bss', 'n/a')}")
print(f"  account valid: {acct.get('valid', 'n/a')}")
