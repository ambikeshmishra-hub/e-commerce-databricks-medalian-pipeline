# AI Prompts — Gold Layer

## Prompt 1: Sales by Product Gold Mart

**PROMPT SENT:**
"@spec.md @.cursorrules
Structure: Create `src/gold/01_sales_by_product.sql`.
Purpose: Define the Databricks Spark SQL query to create the sales by product analytical mart[cite: 1].

Requirements:
1. Write a `CREATE OR REPLACE TABLE gold_sales_by_product AS` statement.
2. Sourced table: `silver_orders` joined with `bronze_products` on `product_id`.
3. Strict Filter: Filter source data where `quality_check_result = 'PASS'`[cite: 1].
4. Group by: `product_id`, `product_name`, and `category`[cite: 1].
5. Aggregate columns to compute:
   - `total_orders`: COUNT of `order_id`[cite: 1]
   - `total_revenue`: SUM of `total_amount` rounded to 2 decimal places[cite: 1]
   - `avg_order_value`: AVG of `total_amount` rounded to 2 decimal places[cite: 1]
6. Ensure standard ANSI/Spark SQL syntax formatted cleanly with proper table aliases.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/gold/01_sales_by_product.sql` with `CREATE OR REPLACE TABLE workspace.gold.gold_sales_by_product AS` sourcing PASS rows from `workspace.silver.silver_orders` joined to `workspace.bronze.bronze_products`, grouped by product dimensions with `total_orders`, `total_revenue`, and `avg_order_value` aggregates.

Deployed and executed on Databricks:
- SQL file: `/Shared/medallion-pipeline/src/gold/01_sales_by_product.sql`
- Notebook: `/Shared/medallion-pipeline/gold/01_sales_by_product`
- Job submit via `conf/gold_01_sales_by_product_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/656060766263682/run/525898651215230

**YOUR EVALUATION:**
✓ **What was good:**
- Gold layer sources only `quality_check_result = 'PASS'` per `.cursorrules`
- Clean Spark SQL with table aliases `o` / `p`
- Rounded revenue metrics to 2 decimal places

**FINAL DECISION:**
✅ **Accepted** — `workspace.gold.gold_sales_by_product` mart created successfully.

---

## Prompt 2: Revenue by Customer Gold Mart

**PROMPT SENT:**
"@spec.md @.cursorrules
Structure: Create `src/gold/02_revenue_by_customer.sql`.
Purpose: Define the Databricks Spark SQL query to create the customer revenue analytical mart[cite: 1].

Requirements:
1. Write a `CREATE OR REPLACE TABLE gold_revenue_by_customer AS` statement.
2. Sourced table: `silver_orders` joined with `bronze_customers` on `customer_id`.
3. Strict Filter: Include ONLY clean records (`WHERE quality_check_result = 'PASS'`)[cite: 1].
4. Group by: `customer_id`, `customer_name`, and `customer_segment`[cite: 1].
5. Aggregate columns to compute:
   - `total_orders`: COUNT of `order_id`[cite: 1]
   - `total_revenue`: SUM of `total_amount` rounded to 2 decimal places[cite: 1]
   - `avg_order_value`: AVG of `total_amount` rounded to 2 decimal places[cite: 1]
   - `lifetime_value_actual`: AVG of customer `lifetime_value` rounded to 2 decimal places[cite: 1]
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/gold/02_revenue_by_customer.sql` with `CREATE OR REPLACE TABLE workspace.gold.gold_revenue_by_customer AS` sourcing PASS rows from `workspace.silver.silver_orders` joined to `workspace.bronze.bronze_customers`, grouped by customer dimensions with `total_orders`, `total_revenue`, `avg_order_value`, and `lifetime_value_actual` aggregates.

Deployed and executed on Databricks:
- SQL file: `/Shared/medallion-pipeline/src/gold/02_revenue_by_customer.sql`
- Notebook: `/Shared/medallion-pipeline/gold/02_revenue_by_customer`
- Job submit via `conf/gold_02_revenue_by_customer_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/1118461978639542/run/868195166949999

**YOUR EVALUATION:**
✓ **What was good:**
- Gold layer sources only `quality_check_result = 'PASS'` per `.cursorrules`
- Clean Spark SQL with table aliases `o` / `c`
- Includes `lifetime_value_actual` from bronze customer dimension

**FINAL DECISION:**
✅ **Accepted** — `workspace.gold.gold_revenue_by_customer` mart created successfully.

---

## Prompt 3: Daily & Weekly Trends Gold Mart

**PROMPT SENT:**
"@spec.md @.cursorrules
Structure: Create `src/gold/03_daily_weekly_trends.sql`.
Purpose: Define the Databricks Spark SQL query to aggregate chronological order trends for time-series analytics.

Requirements:
1. Write a `CREATE OR REPLACE TABLE gold_daily_weekly_trends AS` statement.
2. Source data strictly from `silver_orders` where `quality_check_result = 'PASS'`.
3. Columns to project:
   - `order_date`: Cast as DATE
   - `order_week`: `DATE_TRUNC('week', CAST(order_date AS DATE))`
   - `daily_order_count`: COUNT of `order_id`
   - `daily_revenue`: SUM of `total_amount` rounded to 2 decimal places
4. Group by `order_date` and `DATE_TRUNC('week', CAST(order_date AS DATE))`.
5. Order by `order_date ASC`.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/gold/03_daily_weekly_trends.sql` with `CREATE OR REPLACE TABLE workspace.gold.gold_daily_weekly_trends AS` sourcing PASS rows from `workspace.silver.silver_orders`, projecting daily/weekly dimensions and `daily_order_count` / `daily_revenue` aggregates, ordered by `order_date ASC`.

Deployed and executed on Databricks:
- SQL file: `/Shared/medallion-pipeline/src/gold/03_daily_weekly_trends.sql`
- Notebook: `/Shared/medallion-pipeline/gold/03_daily_weekly_trends`
- Job submit via `conf/gold_03_daily_weekly_trends_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/205331145306624/run/412920360396157

**YOUR EVALUATION:**
✓ **What was good:**
- Gold layer sources only `quality_check_result = 'PASS'` per `.cursorrules`
- Time-series dimensions via `CAST(order_date AS DATE)` and `DATE_TRUNC('week', ...)`
- Chronological ordering for dashboard consumption

**FINAL DECISION:**
✅ **Accepted** — `workspace.gold.gold_daily_weekly_trends` mart created successfully.

---

## Prompt 4: Customer Segmentation Gold Mart

**PROMPT SENT:**
"@spec.md @.cursorrules
Structure: Create `src/gold/04_customer_segmentation.sql`.
Purpose: Define the Databricks Spark SQL query to aggregate customer behavior into business segments[cite: 1].

Requirements:
1. Write a `CREATE OR REPLACE TABLE gold_customer_segmentation AS` statement.
2. Use a Common Table Expression (CTE) to first aggregate customer-level orders and total revenue from `silver_orders` where `quality_check_result = 'PASS'`.
3. Apply a CASE statement to determine `segment_type`:
   - 'High-Value' when `total_revenue > 3000`
   - 'Repeat' when `total_orders > 5`
   - 'One-Time' when `total_orders = 1`
   - 'Inactive' for all other cases[cite: 1]
4. Final SELECT statement grouping by `segment_type` to calculate:
   - `customer_count`: COUNT of distinct customers[cite: 1]
   - `avg_revenue`: AVG of `total_revenue` rounded to 2 decimal places[cite: 1]
   - `total_revenue`: SUM of `total_revenue` rounded to 2 decimal places[cite: 1]"

**AI RESPONSE SUMMARY:**
Created `src/gold/04_customer_segmentation.sql` with CTEs `customer_orders` (PASS-only aggregation) and `segmented_customers` (CASE-based `segment_type`), final SELECT grouped by segment with `customer_count`, `avg_revenue`, and `total_revenue`.

Deployed and executed on Databricks:
- SQL file: `/Shared/medallion-pipeline/src/gold/04_customer_segmentation.sql`
- Notebook: `/Shared/medallion-pipeline/gold/04_customer_segmentation`
- Job submit via `conf/gold_04_customer_segmentation_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/817652295484571/run/303105634878196

**YOUR EVALUATION:**
✓ **What was good:**
- Gold layer sources only `quality_check_result = 'PASS'` per `.cursorrules`
- CTE pattern separates customer aggregation from segment assignment
- CASE precedence correctly prioritizes High-Value before Repeat

**FINAL DECISION:**
✅ **Accepted** — `workspace.gold.gold_customer_segmentation` mart created successfully.

---

## Prompt 5: Create Gold Tables Orchestrator

**PROMPT SENT:**
"@spec.md @.cursorrules @src/gold/
Structure: Create `src/gold/create_gold_tables.py`.
Purpose: PySpark runner script that executes all four `.sql` files to materialize the Gold tables in Databricks[cite: 1].

Requirements:
1. Initialize or get the active `SparkSession`.
2. Implement a helper function `execute_sql_file(spark: SparkSession, filepath: str)` that reads the SQL query text from disk and executes it via `spark.sql(query)`[cite: 1].
3. Execute the 4 files sequentially:
   - `src/gold/01_sales_by_product.sql`[cite: 1]
   - `src/gold/02_revenue_by_customer.sql`[cite: 1]
   - `src/gold/03_daily_weekly_trends.sql`
   - `src/gold/04_customer_segmentation.sql`[cite: 1]
4. Add progress print statements before and after each execution showing table materialization status.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/gold/create_gold_tables.py` with `execute_sql_file()` and `run_gold_pipeline()` executing all four SQL files sequentially with before/after progress logging and row counts per table.

Deployed and executed on Databricks:
- Module: `/Shared/medallion-pipeline/src/gold/create_gold_tables.py`
- Notebook: `/Shared/medallion-pipeline/gold/create_gold_tables`
- Job submit via `conf/gold_create_gold_tables_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/792841899064452/run/966980266915299

**YOUR EVALUATION:**
✓ **What was good:**
- Reusable `execute_sql_file` helper for SQL-driven gold marts
- Sequential orchestration with clear progress logging
- Resolves local vs Databricks workspace SQL paths automatically

**FINAL DECISION:**
✅ **Accepted** — gold orchestrator materializes all four tables successfully.
