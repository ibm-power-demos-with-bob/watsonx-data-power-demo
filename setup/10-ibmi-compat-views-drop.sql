-- ============================================================================
-- 10b. IBM i — Drop compatibility views (run before re-creating)
-- ============================================================================
-- Only run this when the views already exist and you need to recreate them.
-- On first install, skip this file and run 10-ibmi-compat-views.sql directly.
-- ============================================================================
DROP VIEW OLIST.V_CUSTOMERS;
DROP VIEW OLIST.V_PRODUCTS;
DROP VIEW OLIST.V_ORDERS;
DROP VIEW OLIST.V_ORDERITEMS;
