# Databricks SQL Dashboard Setup Guide

Step-by-step instructions for building the E-Commerce Medallion Pipeline dashboard
using queries from `src/dashboard/dashboard_queries.sql` against Gold-layer tables
in the `workspace` catalog.

## Prerequisites

1. Gold tables are materialized in Databricks:
   - `workspace.gold.gold_sales_by_product`
   - `workspace.gold.gold_revenue_by_customer`
   - `workspace.gold.gold_customer_segmentation`
2. Run `src/gold/create_gold_tables.py` (or the gold orchestrator notebook) if
   tables are missing.
3. Open the Databricks workspace: **SQL** → **SQL Editor**.

---

## Part 1: Create the Three SQL Queries

Create one saved query per tile. Copy each query block from
`dashboard_queries.sql` (or use the queries below).

### Query 1 — `dq_tile1_top10_products`

```sql
SELECT
    product_name,
    category,
    total_revenue
FROM workspace.gold.gold_sales_by_product
ORDER BY total_revenue DESC
LIMIT 10;
```

### Query 2 — `dq_tile2_revenue_distribution`

```sql
SELECT
    CASE
        WHEN total_revenue <= 500 THEN '0 - 500'
        WHEN total_revenue <= 1500 THEN '500 - 1500'
        WHEN total_revenue <= 3000 THEN '1501 - 3000'
        ELSE '3000+'
    END AS revenue_bucket,
    COUNT(*) AS customer_count
FROM workspace.gold.gold_revenue_by_customer
GROUP BY 1
ORDER BY
    CASE revenue_bucket
        WHEN '0 - 500' THEN 1
        WHEN '500 - 1500' THEN 2
        WHEN '1501 - 3000' THEN 3
        WHEN '3000+' THEN 4
    END;
```

### Query 3 — `dq_tile3_customer_segmentation`

```sql
SELECT
    segment_type,
    customer_count,
    total_revenue
FROM workspace.gold.gold_customer_segmentation
ORDER BY
    CASE segment_type
        WHEN 'High-Value' THEN 1
        WHEN 'Repeat' THEN 2
        WHEN 'One-Time' THEN 3
        WHEN 'Inactive' THEN 4
    END;
```

For each query:

1. Paste into **SQL Editor**.
2. Set **Default catalog** to `workspace` (if prompted).
3. Click **Run** to validate results.
4. Click **Save** → name the query as shown above.

---

## Part 2: Create the Dashboard

1. Go to **SQL** → **Dashboards**.
2. Click **Create dashboard**.
3. Name it `E-Commerce Gold Analytics`.
4. Click **Add** → **Visualization** for each tile below.

---

## Tile 1 — Top 10 Products by Revenue

**Visual intent:** Rank highest-revenue products in a horizontal bar chart for
merchandising and inventory focus.

| Setting | Value |
|---|---|
| **Query** | `dq_tile1_top10_products` |
| **Chart type** | **Bar** |
| **Orientation** | **Horizontal** (swap X/Y for horizontal bars) |
| **X-Axis** | `total_revenue` |
| **Y-Axis** | `product_name` |
| **Color** | `category` |
| **Sort** | `total_revenue` descending (already in query) |

### UI steps

1. Add visualization → select `dq_tile1_top10_products`.
2. Open the **Visualization** tab.
3. Set **Chart type** to **Bar**.
4. Under **Chart configuration**:
   - **X-Axis**: `total_revenue`
   - **Y-Axis**: `product_name`
   - **Color**: `category`
5. Enable **Horizontal orientation** (label may appear as **Swap axes** or
   **Horizontal bar** depending on UI version).
6. Title the tile: **Top 10 Products by Revenue**.
7. Click **Save**.

---

## Tile 2 — Customer Revenue Distribution

**Visual intent:** Show customer concentration across revenue tiers as a column
chart (histogram-style buckets).

| Setting | Value |
|---|---|
| **Query** | `dq_tile2_revenue_distribution` |
| **Chart type** | **Bar** / **Column** |
| **X-Axis** | `revenue_bucket` |
| **Y-Axis** | `customer_count` |
| **Sort** | Logical bucket order (built into query) |

### UI steps

1. Add visualization → select `dq_tile2_revenue_distribution`.
2. Set **Chart type** to **Bar** (vertical columns).
3. Under **Chart configuration**:
   - **X-Axis**: `revenue_bucket`
   - **Y-Axis**: `customer_count`
4. Disable automatic alphabetical sort on X-axis if the UI overrides query
   order; keep buckets in `0 - 500` → `3000+` sequence.
5. Title the tile: **Customer Revenue Distribution**.
6. Click **Save**.

---

## Tile 3 — Customer Segmentation Breakdown

**Visual intent:** Compare segment share by customer count with revenue context in
tooltips for marketing and retention planning.

| Setting | Value |
|---|---|
| **Query** | `dq_tile3_customer_segmentation` |
| **Chart type** | **Pie** or **Donut** |
| **Slice dimension** | `segment_type` |
| **Value** | `customer_count` |
| **Tooltip** | `total_revenue` |

### UI steps

1. Add visualization → select `dq_tile3_customer_segmentation`.
2. Set **Chart type** to **Pie** or **Donut**.
3. Under **Chart configuration**:
   - **Slice dimension** (or **Group by**): `segment_type`
   - **Value** (or **Measure**): `customer_count`
   - **Tooltip**: add `total_revenue` as an additional field
4. Title the tile: **Customer Segmentation Breakdown**.
5. Click **Save**.

---

## Part 3: Parameter Filters (Date Range & Category)

Dashboard parameters let viewers filter tiles without editing SQL. Add parameters
at the dashboard level, then reference them in parameterized query versions.

### Step A — Add dashboard parameters

1. Open the dashboard → **Edit**.
2. Click **Add parameter** (or **Filters** → **Add**).
3. Create parameters:

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `start_date` | Date | `2023-01-01` | Order period start |
| `end_date` | Date | `2024-12-31` | Order period end |
| `category` | Query / Dropdown | `All` | Product category filter |

For the **category** dropdown, create a helper query `dq_param_categories`:

```sql
SELECT DISTINCT category
FROM workspace.gold.gold_sales_by_product
ORDER BY category;
```

Bind the `category` parameter to this query's `category` column.

### Step B — Parameterized Tile 1 query

Replace Tile 1's saved query with a parameterized version when date/category
filtering is required:

```sql
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(o.total_amount), 2) AS total_revenue
FROM workspace.silver.silver_orders AS o
INNER JOIN workspace.bronze.bronze_products AS p
    ON o.product_id = p.product_id
WHERE o.quality_check_result = 'PASS'
  AND CAST(o.order_date AS DATE) BETWEEN :start_date AND :end_date
  AND (:category = 'All' OR p.category = :category)
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;
```

> **Note:** Parameterized queries read from Silver/Bronze to apply date filters.
> Gold marts are pre-aggregated snapshots; use them for static tiles or rebuild
> gold tables on a schedule when filters must stay gold-only.

### Step C — Wire parameters to the dashboard

1. In dashboard **Edit** mode, open each parameter's settings.
2. Map `start_date` and `end_date` to the parameterized query placeholders
   `:start_date` and `:end_date`.
3. Map `category` to `:category` on Tile 1 (and any other product-level tiles).
4. Set **Apply** behavior to **Auto** or **Apply button** per your preference.
5. **Publish** the dashboard and test each filter combination.

### Parameter tips

- Use **Date** type for `start_date` / `end_date` to render a calendar picker.
- Use **Query** type for `category` to populate a dropdown from live data.
- Add a sentinel value `All` in the category parameter default so one query
  serves both filtered and unfiltered views.
- Tiles 2 and 3 can remain static (gold-only) or be extended with similar
  `BETWEEN :start_date AND :end_date` filters on underlying silver joins.

---

## Part 4: Publish and Share

1. Click **Publish** on the dashboard.
2. Use **Share** to grant access to analysts or stakeholders.
3. Optionally schedule gold table refreshes via **Workflows** so dashboard data
   stays current after bronze/silver pipeline runs.

---

## Workspace Paths (Databricks)

| Asset | Path |
|---|---|
| SQL queries file | `/Shared/medallion-pipeline/src/dashboard/dashboard_queries.sql` |
| This guide | `/Shared/medallion-pipeline/src/dashboard/DASHBOARD_GUIDE.md` |
| Validation notebook | `/Shared/medallion-pipeline/dashboard/dashboard_guide` |

Run the validation notebook to confirm all three tile queries execute successfully
before wiring the Databricks SQL Dashboard UI.
