-- Medallion pipeline — Unity Catalog schema bootstrap
-- Run in Databricks SQL Editor or via spark.sql() before pipeline execution.
-- Delta tables are created by bronze/silver/gold pipeline jobs (CTAS), not here.

CREATE SCHEMA IF NOT EXISTS workspace.bronze
COMMENT 'Bronze layer: lossless raw CSV ingest with audit metadata';

CREATE SCHEMA IF NOT EXISTS workspace.silver
COMMENT 'Silver layer: soft-quarantine DQ with dq_errors and quality_check_result';

CREATE SCHEMA IF NOT EXISTS workspace.gold
COMMENT 'Gold layer: PASS-only analytical marts';

-- Source CSV volume (create once if not present)
-- CREATE VOLUME IF NOT EXISTS workspace.default.medallion_data;

-- Expected pipeline-managed tables (created by jobs, documented for reference):
-- workspace.bronze.bronze_customers
-- workspace.bronze.bronze_orders
-- workspace.bronze.bronze_products
-- workspace.silver.silver_orders
-- workspace.gold.gold_sales_by_product
-- workspace.gold.gold_revenue_by_customer
-- workspace.gold.gold_daily_weekly_trends
-- workspace.gold.gold_customer_segmentation
