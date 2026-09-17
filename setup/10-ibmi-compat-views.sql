-- ============================================================================
-- 10. IBM i Db2 — Compatibility views for watsonx.data federation
-- ============================================================================
-- Purpose:
--   watsonx.data's Db2 for i connector cannot map IBM i CHAR(N) columns to
--   Presto types — it throws "Unknown type char(32)" during table scans.
--   Native VARCHAR columns scan successfully.
--
--   These views expose every CHAR(32) identifier column (UUIDs and hash keys)
--   as VARCHAR(32), and every CHAR(5)/CHAR(2) as VARCHAR(5)/VARCHAR(2).
--   All other columns pass through unchanged from the base tables.
--
--   The connector is then pointed at these views, not the base tables, for
--   any query that touches the affected columns.
--
-- Schema:   OLIST
-- Views:    V_CUSTOMERS  V_PRODUCTS  V_ORDERS  V_ORDERITEMS
--
-- Run via:
--   python setup/6-load-ibmi-olist.py --host <fqdn> --user <user> \
--       --key <key> --run-sql setup/10-ibmi-compat-views.sql
-- OR manually via SSH:
--   cat setup/10-ibmi-compat-views.sql | ssh -i <key> <user>@<host> \
--       "cat > /tmp/compat_views.sql && system \"RUNSQLSTM SRCSTMF('/tmp/compat_views.sql') COMMIT(*NONE)\""
-- ============================================================================
-- NOTE: DROP statements are in 10-ibmi-compat-views-drop.sql (run first on
-- re-runs only; skip on first install since the views do not yet exist).


-- ---------------------------------------------------------------------------
-- V_CUSTOMERS
-- CHAR(32) → VARCHAR(32):  CUSTID, CUSTUNIQ
-- CHAR(5)  → VARCHAR(5):   ZIPCODE
-- CHAR(2)  → VARCHAR(2):   STATE
-- ---------------------------------------------------------------------------
CREATE VIEW OLIST.V_CUSTOMERS AS
  SELECT
    CAST(CUSTID   AS VARCHAR(32)) AS "customer id",
    CAST(CUSTUNIQ AS VARCHAR(32)) AS "customer unique id",
    CAST(ZIPCODE  AS VARCHAR(5))  AS "zip code prefix",
    CITY                          AS "city",
    CAST(STATE    AS VARCHAR(2))  AS "state"
  FROM OLIST.CUSTOMERS;

-- ---------------------------------------------------------------------------
-- V_PRODUCTS
-- CHAR(32) → VARCHAR(32):  PRODID
-- ---------------------------------------------------------------------------
CREATE VIEW OLIST.V_PRODUCTS AS
  SELECT
    CAST(PRODID   AS VARCHAR(32))  AS "product id",
    CATPT                          AS "category (pt)",
    CATEN                          AS "category (en)",
    NAMELEN                        AS "name length",
    DESCLEN                        AS "desc length",
    PHOTOQTY                       AS "photos qty",
    WEIGHTG                        AS "weight g",
    LENGTHCM                       AS "length cm",
    HEIGHTCM                       AS "height cm",
    WIDTHCM                        AS "width cm",
    SECTOR                         AS "sector"
  FROM OLIST.PRODUCTS;

-- ---------------------------------------------------------------------------
-- V_ORDERS
-- CHAR(32) → VARCHAR(32):  ORDERID, CUSTID
-- ---------------------------------------------------------------------------
CREATE VIEW OLIST.V_ORDERS AS
  SELECT
    CAST(ORDERID  AS VARCHAR(32))  AS "order id",
    CAST(CUSTID   AS VARCHAR(32))  AS "customer id",
    STATUS                         AS "order status",
    PURCHTS                        AS "purchase timestamp",
    APPRVTS                        AS "approved at",
    DLVCARR                        AS "delivered carrier",
    DLVCUST                        AS "delivered customer",
    ESTDLV                         AS "estimated delivery"
  FROM OLIST.ORDERS;

-- ---------------------------------------------------------------------------
-- V_ORDERITEMS
-- CHAR(32) → VARCHAR(32):  ORDERID, PRODID, SELLERID
-- ---------------------------------------------------------------------------
CREATE VIEW OLIST.V_ORDERITEMS AS
  SELECT
    CAST(ORDERID  AS VARCHAR(32))  AS "order id",
    ITEMID                         AS "order item id",
    CAST(PRODID   AS VARCHAR(32))  AS "product id",
    CAST(SELLERID AS VARCHAR(32))  AS "seller id",
    SHIPLMT                        AS "ship limit date",
    PRICE                          AS "price",
    FREIGHT                        AS "freight value"
  FROM OLIST.ORDERITEMS;

-- ============================================================================
-- Quick smoke-test queries — run these after creation to confirm success:
--
--   SELECT "customer id", "state" FROM OLIST.V_CUSTOMERS FETCH FIRST 3 ROWS ONLY;
--   SELECT "product id", "sector" FROM OLIST.V_PRODUCTS  FETCH FIRST 3 ROWS ONLY;
--   SELECT "order id", "order status" FROM OLIST.V_ORDERS FETCH FIRST 3 ROWS ONLY;
--   SELECT "order id", "product id"   FROM OLIST.V_ORDERITEMS FETCH FIRST 3 ROWS ONLY;
-- ============================================================================
