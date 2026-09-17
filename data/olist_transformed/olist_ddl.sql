-- ============================================================================
-- 5. IBM i Db2 DDL — Olist Retail Dataset
-- ============================================================================
-- Run via setup/6-load-ibmi-olist.py --create-schema
-- OR manually via the VSCode "IBM i Development Pack" extension (Run SQL Scripts).
--
-- Uses NAMING(*SQL) dot notation throughout — required for RUNSQLSTM.
-- RCDFMT record format names follow IBM i conventions (max 10 chars).
-- ============================================================================

CREATE SCHEMA OLIST;

-- ---------------------------------------------------------------------------
-- CUSTOMERS — olist_customers_dataset.csv
-- ---------------------------------------------------------------------------
CREATE TABLE OLIST.CUSTOMERS
(
  "Customer ID"         FOR COLUMN CUSTID    CHAR(32)     NOT NULL,
  "Customer Unique ID"  FOR COLUMN CUSTUNIQ  CHAR(32)     NOT NULL,
  "Zip Code Prefix"     FOR COLUMN ZIPCODE   CHAR(5),
  "City"                FOR COLUMN CITY      VARCHAR(60),
  "State"               FOR COLUMN STATE     CHAR(2),
  PRIMARY KEY (CUSTID)
)
RCDFMT CUSTOMERR;

-- ---------------------------------------------------------------------------
-- PRODUCTS — olist_products_dataset.csv + product_category_name_translation.csv
-- ---------------------------------------------------------------------------
CREATE TABLE OLIST.PRODUCTS
(
  "Product ID"          FOR COLUMN PRODID    CHAR(32)     NOT NULL,
  "Category (PT)"       FOR COLUMN CATPT     VARCHAR(60),
  "Category (EN)"       FOR COLUMN CATEN     VARCHAR(60),
  "Name Length"         FOR COLUMN NAMELEN   SMALLINT,
  "Desc Length"         FOR COLUMN DESCLEN   INTEGER,
  "Photos Qty"          FOR COLUMN PHOTOQTY  SMALLINT,
  "Weight g"            FOR COLUMN WEIGHTG   DECIMAL(10,2),
  "Length cm"           FOR COLUMN LENGTHCM  DECIMAL(8,2),
  "Height cm"           FOR COLUMN HEIGHTCM  DECIMAL(8,2),
  "Width cm"            FOR COLUMN WIDTHCM   DECIMAL(8,2),
  PRIMARY KEY (PRODID)
)
RCDFMT PRODUCTR;

-- ---------------------------------------------------------------------------
-- ORDERS — olist_orders_dataset.csv
-- ---------------------------------------------------------------------------
CREATE TABLE OLIST.ORDERS
(
  "Order ID"              FOR COLUMN ORDERID   CHAR(32)     NOT NULL,
  "Customer ID"           FOR COLUMN CUSTID    CHAR(32)     NOT NULL,
  "Order Status"          FOR COLUMN STATUS    VARCHAR(20),
  "Purchase Timestamp"    FOR COLUMN PURCHTS   TIMESTAMP,
  "Approved At"           FOR COLUMN APPRVTS   TIMESTAMP,
  "Delivered Carrier"     FOR COLUMN DLVCARR   TIMESTAMP,
  "Delivered Customer"    FOR COLUMN DLVCUST   TIMESTAMP,
  "Estimated Delivery"    FOR COLUMN ESTDLV    TIMESTAMP,
  PRIMARY KEY (ORDERID),
  CONSTRAINT ORDCUSTFK FOREIGN KEY (CUSTID)
      REFERENCES OLIST.CUSTOMERS (CUSTID)
      ON DELETE RESTRICT
)
RCDFMT ORDERR;

-- ---------------------------------------------------------------------------
-- ORDER_ITEMS — olist_order_items_dataset.csv
-- ---------------------------------------------------------------------------
CREATE TABLE OLIST.ORDERITEMS
(
  "Order ID"            FOR COLUMN ORDERID   CHAR(32)     NOT NULL,
  "Order Item ID"       FOR COLUMN ITEMID    SMALLINT     NOT NULL,
  "Product ID"          FOR COLUMN PRODID    CHAR(32)     NOT NULL,
  "Seller ID"           FOR COLUMN SELLERID  CHAR(32),
  "Ship Limit Date"     FOR COLUMN SHIPLMT   TIMESTAMP,
  "Price"               FOR COLUMN PRICE     DECIMAL(10,2),
  "Freight Value"       FOR COLUMN FREIGHT   DECIMAL(10,2),
  PRIMARY KEY (ORDERID, ITEMID),
  CONSTRAINT OIORDERFK FOREIGN KEY (ORDERID)
      REFERENCES OLIST.ORDERS (ORDERID)
      ON DELETE CASCADE,
  CONSTRAINT OIPRODFK  FOREIGN KEY (PRODID)
      REFERENCES OLIST.PRODUCTS (PRODID)
      ON DELETE RESTRICT
)
RCDFMT ORDERITMR;

-- ---------------------------------------------------------------------------
-- Indexes for federated query patterns
-- ---------------------------------------------------------------------------
CREATE INDEX OLIST.IXORDCUST  ON OLIST.ORDERS     (CUSTID);
CREATE INDEX OLIST.IXOIPROD   ON OLIST.ORDERITEMS (PRODID);
CREATE INDEX OLIST.IXORDSTAT  ON OLIST.ORDERS     (STATUS, PURCHTS);
