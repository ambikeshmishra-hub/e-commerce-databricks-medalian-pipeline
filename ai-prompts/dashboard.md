# AI Prompts — Dashboard

## Prompt 1: Dashboard BI Tile Queries

**PROMPT SENT:**
"@spec.md @.cursorrules @src/gold/
Structure: Create `src/dashboard/dashboard_queries.sql`.
Purpose: Provide production-ready Databricks SQL queries for 3 BI dashboard visual tiles sourced directly from Gold tables[cite: 1].

Requirements:
1. Tile 1 Query (Horizontal Bar Chart): Top 10 Products by Revenue.
   - Sourced from `gold_sales_by_product`[cite: 1].
   - Columns: `product_name`, `category`, `total_revenue`[cite: 1].
   - Order by `total_revenue DESC` with `LIMIT 10`[cite: 1].
2. Tile 2 Query (Histogram / Column Chart): Customer Revenue Distribution.
   - Sourced from `gold_revenue_by_customer`[cite: 1].
   - Bucket `total_revenue` into 4 tiers: '0 - 500', '500 - 1500', '1501 - 3000', '3000+'[cite: 1].
   - Calculate `customer_count` per bucket and order logically[cite: 1].
3. Tile 3 Query (Pie / Donut Chart): Customer Segmentation Breakdown.
   - Sourced from `gold_customer_segmentation`[cite: 1].
   - Columns: `segment_type`, `customer_count`, `total_revenue`[cite: 1].
4. Format queries cleanly with comments explaining the visual intent of each tile[cite: 1].
also do it on databricks & execute there"

**AI RESPONSE SUMMARY:**
Created `src/dashboard/dashboard_queries.sql` with three commented BI tile queries sourcing `workspace.gold` tables, plus `run_dashboard_queries.py` and notebook to parse/execute all tiles with progress output on Databricks.

Deployed and executed on Databricks:
- SQL file: `/Shared/medallion-pipeline/src/dashboard/dashboard_queries.sql`
- Notebook: `/Shared/medallion-pipeline/dashboard/dashboard_queries`
- Job submit via `conf/dashboard_queries_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/875670704681647/run/384787975256471

**YOUR EVALUATION:**
✓ **What was good:**
- Queries sourced directly from gold marts per medallion architecture
- Tile comments document visual intent for BI builders
- Revenue buckets ordered logically for histogram display

**FINAL DECISION:**
✅ **Accepted** — all three dashboard tile queries executed successfully on Databricks.

---

## Prompt 2: Dashboard Setup Guide

**PROMPT SENT:**
"@src/dashboard/dashboard_queries.sql
Structure: Create `src/dashboard/DASHBOARD_GUIDE.md`.
Purpose: Provide step-by-step documentation explaining how to configure the 3 visual tiles in the Databricks SQL Dashboard UI[cite: 1].

Requirements:
1. Provide UI setup steps for Tile 1 (Top 10 Products): Chart Type (Bar), X-Axis (`total_revenue`), Y-Axis (`product_name`), Color (`category`)[cite: 1].
2. Provide UI setup steps for Tile 2 (Revenue Distribution): Chart Type (Histogram/Column), X-Axis (`revenue_bucket`), Y-Axis (`customer_count`)[cite: 1].
3. Provide UI setup steps for Tile 3 (Customer Segmentation): Chart Type (Pie/Donut), Slice Dimension (`segment_type`), Value (`customer_count`), Tooltip (`total_revenue`)[cite: 1].
4. Add instructions on setting up parameter filters (e.g., date range, category dropdown)[cite: 1].
also do it on databricks & execute there"

**AI RESPONSE SUMMARY:**
Created `src/dashboard/DASHBOARD_GUIDE.md` with step-by-step SQL Dashboard UI instructions for all three tiles, parameter filter setup (date range + category dropdown), and publish/share steps. Added `dashboard_guide_nb.py` validation notebook that previews the guide and re-executes all tile queries.

Deployed and executed on Databricks:
- Guide: `/Shared/medallion-pipeline/src/dashboard/DASHBOARD_GUIDE.md`
- Notebook: `/Shared/medallion-pipeline/dashboard/dashboard_guide`
- Job submit via `conf/dashboard_guide_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/1003871303948044/run/610650421134142

**YOUR EVALUATION:**
✓ **What was good:**
- Tile configuration maps directly to `dashboard_queries.sql` columns
- Parameter section documents `:start_date`, `:end_date`, `:category` wiring
- Validation notebook confirms queries run before UI setup

**FINAL DECISION:**
✅ **Accepted** — dashboard guide deployed and tile queries validated on Databricks.

---

## Prompt 3: End-to-End Pipeline + Dashboard Publish

**PROMPT SENT:**
"now create a pipeline on databricks like bronze-layer->silver->gold->dashboard 
execute it on databricks and publish all dashboards on databricks"

**AI RESPONSE SUMMARY:**
Created multi-task Databricks workflow (bronze → silver → gold → dashboard publish), `publish_dashboard.py` using Lakeview REST API to create/publish **E-Commerce Gold Analytics** with 3 widgets, deploy script, and persistent job definition. Deployed to workspace, executed pipeline run **SUCCESS** (all 4 tasks), published dashboard via Lakeview API.

**Artifacts:**
- `conf/medallion_pipeline_run.json` — one-shot submit run
- `conf/medallion_pipeline_job.json` — persistent job (job_id `460413873521986`)
- `conf/publish_dashboard_run.json` — dashboard-only publish
- `src/dashboard/publish_dashboard.py` + `publish_dashboard_nb.py`
- `scripts/deploy_workspace.sh`, `scripts/run_medallion_pipeline.sh`

**Execution:**
- Pipeline run: `medallion_pipeline_bronze_silver_gold_dashboard` — **SUCCESS** (run_id `300921087203158`)
- Tasks: bronze ✓, silver ✓, gold ✓, dashboard publish ✓
- Published dashboard: **E-Commerce Gold Analytics** (dashboard_id `01f1a56b998419c7874820200ea1396a`)
- Dashboard URL: https://dbc-8af8048c-3b55.cloud.databricks.com/sql/dashboardsv3/01f1a56b998419c7874820200ea1396a
- Job URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/460413873521986

**YOUR EVALUATION:**
✓ good

**FINAL DECISION:**
✅ **Accepted** — end-to-end pipeline executed and dashboard published on Databricks.
