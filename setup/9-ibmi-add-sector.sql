-- ============================================================================
-- 9. IBM i Db2 — Add SECTOR classification to OLIST.PRODUCTS
-- ============================================================================
-- Run once against the live IBM i — ALTER + UPDATE, no data reload needed.
-- Data already loaded (99k+ rows).  This adds one column and classifies
-- each product by sector using the existing CATEN (English category) column.
--
-- The SECTOR column is what makes the external signal cross-reference work:
-- when the AI sidecar sees a HIGH severity MARKET_EVENT for affected_sector
-- = 'TECHNOLOGY', it immediately queries IBM i for open orders containing
-- products in that sector — without this column the join has no anchor.
--
-- Run manually via SSH + RUNSQLSTM, or via the VSCode IBM i Dev Pack:
--   RUNSQLSTM SRCSTMF('/tmp/olist/9-ibmi-add-sector.sql')
--             COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(20)
--
-- Idempotent: the ALTER is wrapped in a check; UPDATE is safe to re-run.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Step 1: Add SECTOR column (ignored if column already exists)
-- ---------------------------------------------------------------------------
ALTER TABLE OLIST.PRODUCTS
    ADD COLUMN "Sector" FOR COLUMN SECTOR VARCHAR(30) DEFAULT 'OTHER';

-- ---------------------------------------------------------------------------
-- Step 2: Classify by English category name (CATEN)
-- Sector codes match the affected_sector field in ExternalSignalEvent /
-- signal-injector.py so the sidecar join works without a mapping table.
-- ---------------------------------------------------------------------------
UPDATE OLIST.PRODUCTS SET SECTOR = CASE

    -- Technology / Electronics — maps to IBM profit warning signal
    WHEN CATEN IN (
        'computers_accessories',
        'electronics',
        'telephony',
        'tablets_printing_image',
        'pc_gamer',
        'small_appliances_home_oven_and_coffee',
        'fixed_telephony',
        'audio'
    ) THEN 'TECHNOLOGY'

    -- Logistics / Freight-dependent categories — maps to heatwave / port closure
    WHEN CATEN IN (
        'furniture_decor',
        'furniture_living_room',
        'furniture_bedroom',
        'furniture_mattress_and_upholstery',
        'office_furniture',
        'home_appliances',
        'home_appliances_2',
        'kitchen_dining_laundry_garden_furniture',
        'garden_tools',
        'construction_tools_construction',
        'construction_tools_safety',
        'construction_tools_lights',
        'construction_tools_tools',
        'industry_commerce_and_business'
    ) THEN 'LOGISTICS'

    -- Food & Beverage / Cold chain — also maps to heatwave signal
    WHEN CATEN IN (
        'food',
        'food_drink',
        'drinks',
        'la_cuisine'
    ) THEN 'FOOD_BEVERAGE'

    -- Health & Beauty
    WHEN CATEN IN (
        'health_beauty',
        'perfumery',
        'diapers_and_hygiene',
        'pharmaceuticals'
    ) THEN 'HEALTH_BEAUTY'

    -- Fashion & Apparel
    WHEN CATEN IN (
        'fashion_bags_accessories',
        'fashion_female_clothing',
        'fashion_male_clothing',
        'fashion_shoes',
        'fashion_sport',
        'fashion_underwear_beach',
        'fashion_childrens_clothes'
    ) THEN 'FASHION'

    -- Home Goods
    WHEN CATEN IN (
        'bed_bath_table',
        'housewares',
        'home_confort',
        'home_confort_2',
        'costruction_tools_garden',
        'christmas_supplies',
        'party_supplies',
        'flowers'
    ) THEN 'HOME_GOODS'

    -- Sports & Leisure
    WHEN CATEN IN (
        'sports_leisure',
        'toys',
        'baby',
        'arts_and_craftmanship',
        'musical_instruments',
        'cds_dvds_musicals',
        'dvds_blu_ray',
        'books_general_interest',
        'books_technical',
        'books_imported',
        'stationery'
    ) THEN 'CONSUMER_LEISURE'

    -- Auto
    WHEN CATEN IN (
        'auto',
        'market_place'
    ) THEN 'AUTOMOTIVE'

    ELSE 'OTHER'
END;

-- ---------------------------------------------------------------------------
-- Step 3: Add index to support fast sidecar sector lookups
-- ---------------------------------------------------------------------------
CREATE INDEX OLIST.IXPRODSECT ON OLIST.PRODUCTS (SECTOR);

-- ---------------------------------------------------------------------------
-- Step 4: Verify distribution
-- (Run separately to check — not part of RUNSQLSTM batch)
-- ---------------------------------------------------------------------------
-- SELECT SECTOR, COUNT(*) AS CNT
-- FROM OLIST.PRODUCTS
-- GROUP BY SECTOR
-- ORDER BY CNT DESC;
