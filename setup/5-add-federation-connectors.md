# Federation connector rebuild runbook

This runbook records the tested pattern for rebuilding the watsonx.data federation layer with fresh TechZone resources.

## Architecture

All traffic between on-prem and IBM Cloud flows through a single IBM Cloud Satellite Connector tunnel. The agent on RHEL makes one outbound WebSocket connection to IBM Cloud; that tunnel then carries traffic in **both directions** via two endpoint types:

- **Location endpoints** (IBM Cloud → on-prem): watsonx.data reaches PostgreSQL and IBM i through the tunnel to run federated queries.
- **Cloud endpoints** (on-prem → IBM Cloud): the Demo UI on RHEL reaches the watsonx.data Presto engine through the tunnel, arriving inside the IBM Cloud network where Cloudflare does not block the request.

```
Demo UI (RHEL)
  → localhost:<cloud-endpoint-port>          ← cloud endpoint mapped port
    → Satellite tunnel (agent → IBM Cloud)
      → Presto (*.lakehouse.ibmappdomain.cloud:31618)

watsonx.data Presto (IBM Cloud)
  → c-01.private.eu-gb.link.satellite.cloud.ibm.com:<location-port>
    → Satellite tunnel (IBM Cloud → agent)
      → PostgreSQL (127.0.0.1:5432) / IBM i (<ibmi-ip>:8471)
```

**Why this matters:** the Presto host (`*.lakehouse.ibmappdomain.cloud`) and the watsonx.data REST API (`eu-gb.lakehouse.cloud.ibm.com`) sit behind a Cloudflare policy that rejects requests originating from outside IBM Cloud. Calling them directly from RHEL or a laptop returns Cloudflare error 1010. Routing through the cloud endpoint means the request arrives from inside IBM Cloud and is accepted.

Components:
- watsonx.data SaaS runs in IBM Cloud `eu-gb`.
- RHEL hosts PostgreSQL and the Demo UI.
- IBM i hosts Db2 for i.
- An IBM Cloud Satellite Connector agent runs on RHEL, exposing both location and cloud endpoints.

## Fresh-environment sequence

1. Reserve a combined IBM i + RHEL TechZone environment so both machines share a network.
2. Load the IBM i OLIST schema/data and PostgreSQL OLIST schema/data.
3. Create or obtain the Satellite Connector in the owning IBM Cloud account.
4. Create all three Satellite endpoints **before** starting the agent, so you know the cloud endpoint's assigned target port and can include it in the `podman run` command:

   **Two location endpoints** (IBM Cloud → on-prem):

   | Endpoint name | Type | Destination | Protocol |
   |---|---|---|---|
   | `pg-olist` | location | RHEL `127.0.0.1:5432` | TCP |
   | `ibmi-db2` | location | IBM i `<ibmi-private-ip>:8471` | TCP |

   **One cloud endpoint** (on-prem → IBM Cloud):

   | Endpoint name | Type | Destination | Protocol |
   |---|---|---|---|
   | `wxd-presto` | cloud | `<presto-engine-host>:31618` | TCP |

   The Presto engine host is the per-engine UUID hostname from the watsonx.data console Infrastructure Manager (e.g. `70733fc8-2b02-4683-ba01-628f66e07284.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud`).

   After creating the cloud endpoint, retrieve its assigned **target port** — this is the container-internal port the agent listens on:

   ```bash
   ibmcloud sat endpoints --connector-id <connector-id>
   # Find the port in the Address column for wxd-presto, e.g. TCP :29998
   ```

5. Start the Satellite Connector agent on RHEL as root, **mapping the cloud endpoint's target port** to a host port the Demo UI can reach:

   ```bash
   # Replace 29998 with the actual target port from step 4
   # The left-hand port (e.g. 31618) is what the Demo UI will connect to on localhost
   sudo podman run -d --name wxd-connector-agent --restart always --network host \
     -p 31618:29998 \
     --env SATELLITE_CONNECTOR_ID=<connector-id> \
     --env SATELLITE_CONNECTOR_IAM_APIKEY=<connector-api-key> \
     icr.io/ibm/satellite-connector/satellite-connector-agent:latest
   ```

   With `--network host`, the `-p` flag is actually redundant (host networking means all ports are already on the host), but it documents the intent. If you switch to bridge networking, the `-p` mapping is required.

   After startup, confirm the agent is connected:
   ```bash
   sudo podman logs wxd-connector-agent | grep -E "Connected|Tunnel"
   # Expect: WSR04 Connected, CTB27 Tunnel connected
   ```

6. Verify the agent and endpoint configuration from a machine that has the owning account's API key:

   ```bash
   python setup/satellite-endpoints.py \
     --api-key <satellite-account-api-key> \
     --account-id <satellite-account-guid> \
     --connector-id <connector-id> \
     --ibmi-ip <ibmi-private-ip> \
     --output-json
   ```

   Record the returned `client_host`, `client_port`, endpoint names, destination, and status. The API key is also available locally on the RHEL host through the running agent environment:

   ```bash
   sudo podman inspect wxd-connector-agent \
     --format '{{range .Config.Env}}{{println .}}{{end}}'
   ```

   Never print or commit the API-key value.

7. Complete watsonx.data SaaS setup with the student App ID and a reservation-unique Iceberg catalog name. Wait until the Presto engine is `RUNNING`.
8. Run the connector registration script. Because the watsonx.data REST API is also behind Cloudflare, this script must be run through the cloud endpoint too — or from the watsonx.data GUI (which is the proven fallback). To run via API from RHEL, set `WXD_API_HOST` to `localhost:<mapped-port>` once we have confirmed the cloud endpoint carries HTTPS correctly. For now, use the GUI to register `pg_olist` and `ibmi_olist` as documented in the GUI breakthrough notes in `_checkpoint.md`.

   When API registration via cloud endpoint is confirmed working:

   ```bash
   export WXD_APIKEY=<watsonx-data-service-api-key>
   export WXD_INSTANCE_CRN=<watsonx-data-instance-crn>
   export IBMI_HOST=<satellite-client-host>          # c-01.private.eu-gb.link.satellite.cloud.ibm.com
   export IBMI_PORT=<ibmi-db2-client-port>            # location endpoint port for ibmi-db2
   export IBMI_USERNAME=<ibmi-user>
   export IBMI_PASSWORD=<ibmi-password>
   export PG_HOST=<satellite-client-host>
   export PG_PORT=<pg-olist-client-port>              # location endpoint port for pg-olist
   python3 setup/5-add-federation-connectors.py
   ```

   Use the watsonx.data service API key for `WXD_APIKEY`; do not substitute the Satellite agent key. The script resolves the first running engine and is idempotent by connector name.

9. Update `demo-ui/.env.local` on RHEL to point the Demo UI at the **local cloud endpoint port** rather than the public Presto hostname:

   ```bash
   # .env.local on RHEL
   WXD_PRESTO_HOST=localhost        # cloud endpoint — arrives inside IBM Cloud via tunnel
   WXD_PRESTO_PORT=31618            # host port mapped from cloud endpoint target port
   WXD_APIKEY=<watsonx-data-service-api-key>
   WXD_INSTANCE_CRN=<watsonx-data-instance-crn>
   ```

   With this config the Demo UI's `wxd-query-internal.ts` connects to `localhost:31618`, the Satellite agent tunnels the request into IBM Cloud, and Presto sees it as an internal IBM Cloud request — bypassing Cloudflare entirely.

10. Verify the full chain from RHEL:

    ```bash
    # Quick Presto connectivity check through the cloud endpoint
    curl -s -o /dev/null -w "%{http_code}" \
      -X POST http://localhost:31618/v1/statement \
      -H "Authorization: Bearer $(python3 -c "
    import urllib.request, urllib.parse, json
    d = urllib.parse.urlencode({'grant_type':'urn:ibm:params:oauth:grant-type:apikey','apikey':'<WXD_APIKEY>'}).encode()
    r = urllib.request.Request('https://iam.cloud.ibm.com/identity/token',data=d,headers={'Content-Type':'application/x-www-form-urlencoded'})
    print(json.loads(urllib.request.urlopen(r).read())['access_token'])
    ")" \
      -H "X-Presto-User: ibmlhapikey" \
      --data "SHOW CATALOGS"
    # Expect: 200
    ```

11. Verify in the watsonx.data Query workspace:

    ```sql
    SHOW CATALOGS;
    SHOW SCHEMAS IN pg_olist;
    SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers;
    SHOW SCHEMAS IN ibmi_olist;
    SELECT COUNT(*) FROM ibmi_olist.OLIST.ORDERS;
    ```

12. Run the three-source retail query and then wire the POS generator to the Iceberg catalog.

## Current reservation evidence

For the active combined reservation, the Satellite Connector API returned HTTP 200 using the key held by the running agent. The active account GUID is `ead8711ba2cc4d08a16fd37427f4f01a`; agent `pvm01-e991q02k.56` is healthy. The current endpoints are:

- `pg-olist`: `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` → `127.0.0.1:5432`
- `ibmi-db2`: `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` → `129.40.94.90:8471`

## Troubleshooting

- **Cloudflare error 1010 / HTTP 403 from Presto or the watsonx.data REST API:** the call is arriving from outside IBM Cloud. Do not call `eu-gb.lakehouse.cloud.ibm.com` or `*.lakehouse.ibmappdomain.cloud` directly from RHEL or a laptop. Route through the `wxd-presto` cloud endpoint on `localhost:<mapped-port>` instead.
- **Cloud endpoint not reachable on localhost:** check that the agent container is running (`sudo podman ps`), the target port mapping is correct (`sudo podman inspect wxd-connector-agent`), and the agent logs show `CTB27 Tunnel connected`. With `--network host`, the port is exposed directly on the RHEL host.
- **HTTP 401 from the Satellite endpoint API:** the API key belongs to a different IBM Cloud account than the connector.
- **`Connection failed - Invalid hostname or credentials` from watsonx.data:** verify the registration uses the Satellite `client_host` and `client_port` for the location endpoint, the endpoint is enabled, and the registration was made from within IBM Cloud (GUI, or via cloud endpoint once confirmed working).
- **Direct laptop/RHEL tests to `c-01.private...` time out:** expected — the `.private.` hostname is only resolvable from inside the IBM Cloud private network.
- Test local database reachability from RHEL before registering: PostgreSQL should answer on `127.0.0.1:5432`; IBM i should answer on the reserved IBM i IP and port `8471`.
- Keep the Satellite API key and both database passwords out of the recipe, source control, and chat transcripts. Supply them at run time through TechZone reservation output or environment variables.
