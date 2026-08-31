# Requirements Analysis — E-Commerce Medallion Pipeline

## 1. Problem Statement

An e-commerce retailer operates sales across multiple upstream systems that export **comma-separated value (CSV)** files for three core entities: **customers**, **products**, and **orders**. These files land in object storage and must be ingested into **Databricks** on a recurring basis to support operational reporting, customer analytics, and executive dashboards.

The business problem is not merely moving files into a lakehouse—it is establishing a **trustworthy, auditable analytics foundation** where:

1. **Raw data is preserved** for forensic replay and schema evolution.
2. **Data quality failures are detected and quarantined** without silent row loss.
3. **Gold-layer metrics** reflect only validated transactions so revenue and segmentation KPIs are defensible.

This project implements a **Medallion Architecture** (Bronze → Silver → Gold → Dashboard) on **Delta Lake** with **Unity Catalog** governance, targeting Databricks Community Edition with serverless job execution.

---

## 2. Functional Requirements

### 2.1 Data Generation

| ID | Requirement |
|---|---|
| DG-01 | Generate three CSV datasets: `customers.csv`, `products.csv`, `orders.csv`. |
| DG-02 | Use **Faker**, **NumPy**, and **Pandas** with a fixed random seed (`RANDOM_SEED = 42`) for reproducibility. |
| DG-03 | Inject **exactly 700 intentional data-quality defects** distributed across all three tables per `tool-specific/cursor-workflow/spec.md`. |
| DG-04 | Write NULL values as empty CSV cells (not the string `"null"`). |
| DG-05 | Emit a manifest summary of injected defect categories to stdout after generation. |

### 2.2 Bronze Layer

| ID | Requirement |
|---|---|
| BR-01 | Ingest all three CSVs **losslessly**—no column drops, no row filters, no type coercion beyond Spark CSV inference. |
| BR-02 | Append audit metadata columns: `_ingested_at` (TIMESTAMP) and `_source_file` (STRING). |
| BR-03 | On Databricks, source files from Unity Catalog volume `dbfs:/Volumes/workspace/default/medallion_data/`. |
| BR-04 | Use `_metadata.file_path` (not `input_file_name()`) for source file lineage on UC volumes. |
| BR-05 | Write Delta tables: `workspace.bronze.bronze_customers`, `workspace.bronze.bronze_orders`, `workspace.bronze.bronze_products`. |
| BR-06 | Support idempotent **overwrite** runs with `overwriteSchema` for schema evolution during development. |
| BR-07 | Provide orchestrator (`ingest_all.py`) and per-entity ingest modules with Databricks notebook wrappers. |

### 2.3 Silver Layer

| ID | Requirement |
|---|---|
| SV-01 | Apply modular data-quality checks to `bronze_orders` joined against `bronze_customers` and `bronze_products`. |
| SV-02 | Implement **soft quarantine**: every bronze order row must appear in `silver_orders`—no silent drops. |
| SV-03 | Add `dq_errors` column: `ARRAY<STRING>` containing one or more error tags per failed rule. |
| SV-04 | Add `quality_check_result` column: `'PASS'` when `size(dq_errors) = 0`, else `'FAIL'`. |
| SV-05 | Enforce referential integrity checks via **LEFT OUTER JOIN** only—orphan foreign keys must remain in the dataset. |
| SV-06 | Implement five DQ categories as separate modules: Completeness, Uniqueness, Type Validation, Referential Integrity, Business Logic. |
| SV-07 | Print a pass/fail metrics summary (% passed, % quarantined) after silver table creation. |
| SV-08 | Drop temporary join/count columns before persisting (`row_occurrence_count`, `matched_customer_id`, `matched_product_id`). |

### 2.4 Gold Layer

| ID | Requirement |
|---|---|
| GD-01 | Source **only** rows where `quality_check_result = 'PASS'`. |
| GD-02 | Create four analytical marts: `gold_sales_by_product`, `gold_revenue_by_customer`, `gold_daily_weekly_trends`, `gold_customer_segmentation`. |
| GD-03 | Join to bronze dimension tables where product/customer attributes are needed (gold reads clean facts from silver). |
| GD-04 | Round monetary aggregates to two decimal places. |
| GD-05 | Customer segmentation rules: High-Value (> $3,000 revenue), Repeat (> 5 orders), One-Time (= 1 order), Inactive (else). |

### 2.5 Dashboard

| ID | Requirement |
|---|---|
| DB-01 | Provide three SQL queries for BI tiles: Top 10 Products by Revenue, Customer Revenue Distribution, Customer Segmentation Breakdown. |
| DB-02 | Document visualization intent (bar chart, histogram, pie/donut) in `DASHBOARD_GUIDE.md`. |
| DB-03 | Execute queries against gold tables via `run_dashboard_queries.py` and Databricks notebook wrapper. |

### 2.6 Testing & Validation

| ID | Requirement |
|---|---|
| TS-01 | Integration tests assert bronze row volumes and metadata column population. |
| TS-02 | Integration tests assert silver row parity with bronze (zero row loss). |
| TS-03 | Integration tests assert `FAIL` count > 400 (anomaly detection threshold). |
| TS-04 | Integration tests assert gold revenue columns are positive and non-null. |
| TS-05 | Unit tests cover individual silver DQ helper functions. |

---

## 3. Non-Functional Requirements

### 3.1 Scalability

- Pipeline must scale horizontally on Spark cluster/serverless compute as order volume grows from 50K (dev) to millions (production).
- Modular DQ functions compose via column expressions—no per-row Python callbacks.
- Gold aggregations use Catalyst-optimizable `GROUP BY` and window-free SQL where possible.

### 3.2 Performance

- **No Python UDFs** (`@udf`)—all transformations use native vectorized `pyspark.sql.functions`.
- Avoid `.collect()` on large DataFrames; use `agg()`, `count()`, and `filter()` for metrics.
- Window functions limited to duplicate detection (`count().over(Window.partitionBy(...))`)—acceptable for DQ, not for row explosion.
- Delta `overwrite` mode acceptable for assessment; production would migrate to merge/append with partitioning.

### 3.3 Catalyst Optimization

- DQ rules return `Column` expressions composed into `array()` + `array_filter()`—fully Catalyst-plannable.
- `try_cast(... AS DOUBLE)` for safe numeric validation without ANSI cast exceptions on dirty strings.
- Gold SQL uses explicit `CAST`, `DATE_TRUNC`, and `CASE` expressions Spark can push into Delta scans.

### 3.4 Idempotency

- Bronze, silver, and gold jobs use `CREATE OR REPLACE` / Delta `overwrite` so re-running produces consistent table state from the same source CSVs.
- Fixed random seed ensures identical synthetic CSVs across regeneration runs.
- Job JSON configs in `conf/` provide repeatable Databricks serverless execution.

### 3.5 Zero Data Loss

- Bronze: ingest every CSV row verbatim.
- Silver: **never filter out** bad rows—flag with `quality_check_result = 'FAIL'`.
- Gold: filter only at read time for analytics; silver retains full history for audit.

### 3.6 Observability

- Bronze metadata (`_ingested_at`, `_source_file`) enables lineage tracing.
- Silver `dq_errors` array provides per-row failure reasons.
- `print_dq_metrics_summary()` emits human-readable pass/quarantine percentages.

### 3.7 Security & Governance

- Unity Catalog schema isolation (`workspace.bronze`, `workspace.silver`, `workspace.gold`).
- No hardcoded credentials—Databricks CLI profile `community` in `~/.databrickscfg`.
- Synthetic data only—no real PII in seed datasets.

---

## 4. Assumptions

| ID | Assumption |
|---|---|
| A-01 | All monetary values are in **USD** with two decimal precision. |
| A-02 | **Transaction lifecycle**: an order progresses through statuses `Pending`, `Shipped`, `Delivered`, `Cancelled`, `Returned`; payment may occur 0–14 days after order date for valid rows. |
| A-03 | `order_id` is the grain of `orders.csv` (one row per order line in this simplified model). |
| A-04 | Customer segments in source data are `Premium`, `Standard`, `Basic`; gold behavioral segments are computed separately. |
| A-05 | CSV files use UTF-8 encoding with header row and comma delimiter. |
| A-06 | Databricks Community Edition with Unity Catalog and serverless compute is the target runtime. |
| A-07 | Timezone for `_ingested_at` follows the Databricks workspace default (UTC). |
| A-08 | Cancelled and returned orders remain in the dataset; gold includes them if they pass silver DQ (valid FKs, positive amounts, etc.). |

---

## 5. Edge Cases

| Edge Case | Expected Behavior |
|---|---|
| **NULL foreign keys** (`customer_id`, `product_id`) | Silver flags `NULL_CUSTOMER_ID` / `NULL_PRODUCT_ID`; row retained with `FAIL`. |
| **Orphan foreign keys** (FK value not in parent table) | LEFT JOIN preserves row; `INVALID_CUSTOMER_ID_FK` / `INVALID_PRODUCT_ID_FK` tagged. |
| **Duplicate `order_id`** | Window count > 1 triggers `DUPLICATE_ORDER_ID`; all duplicate rows flagged. |
| **Non-numeric `quantity`** (e.g., `"N/A"`) | `try_cast` returns NULL; `NON_POSITIVE_QUANTITY` not triggered on cast failure—cast-null rows may pass numeric check (known limitation; bronze retains raw string). |
| **Cancelled orders** | Included in bronze/silver; excluded from gold only if DQ fails, not by status filter. |
| **Payment before order date** | `PAYMENT_BEFORE_ORDER_DATE` error tag; row quarantined. |
| **Future-dated orders** (injected in seed data) | Pass silver checks if FKs and amounts valid; may appear in gold trend tables. |
| **Empty CSV cells** | Read as NULL by Spark CSV reader with `inferSchema`. |
| **Schema drift** (new CSV column) | Bronze `overwriteSchema` captures new columns; silver/gold require code update. |
| **Re-run after partial failure** | Overwrite semantics replace entire Delta table—no duplicate accumulation. |

---

## 6. Clarifications Addressed

### 6.1 Soft Quarantine vs. Hard Drops

**Decision: Soft quarantine.**

| Approach | Description | Chosen? |
|---|---|---|
| **Hard drop** | Filter invalid rows out of silver entirely | ✗ Rejected |
| **Hard fail** | Stop pipeline on first DQ violation | ✗ Rejected |
| **Soft quarantine** | Retain all rows; set `quality_check_result` and `dq_errors` | ✓ **Adopted** |

**Rationale:**

- Hard drops make orphan FK rows **invisible** to auditors and inflate gold KPIs.
- Soft quarantine preserves **row-count parity** between bronze and silver (verified by `test_pipeline.py`).
- Gold layer applies the **single filter** (`PASS` only), creating a clean analytics boundary without destroying evidence.

### 6.2 INNER JOIN vs. LEFT OUTER JOIN for FK Validation

**Decision: LEFT OUTER JOIN with alias columns.**

An early AI-generated approach used `INNER JOIN` to validate foreign keys, which **silently removed** orphan records. This violates zero-data-loss and makes quarantine metrics unreliable. The corrected pattern:

1. `check_foreign_key()` — LEFT JOIN child to distinct parent keys.
2. `flag_invalid_fk()` — emit error when FK is non-null but join key is null.
3. Drop alias columns before write.

### 6.3 UDF vs. Native Functions

**Decision: Native vectorized PySpark only.**

Python `@udf` decorators were rejected per `.cursorrules` due to serialization overhead and Catalyst opt-out. All DQ rules return `Column` expressions.

---

## 7. Out of Scope (Current Phase)

- Real-time streaming ingest (Kafka/Event Hubs).
- Silver tables for `customers` and `products` (only `silver_orders` implemented).
- Delta Live Tables (DLT) orchestration—documented as future improvement.
- Great Expectations integration—documented as future improvement.
- CI/CD via Databricks Repos and GitHub Actions.

---

## 8. Success Criteria

| Criterion | Target |
|---|---|
| Bronze row count equals source CSV row count | 100% |
| Silver row count equals bronze orders row count | 100% |
| Silver quarantined rows detected | > 400 |
| Gold tables populated from PASS rows only | Non-empty, positive revenue |
| All pytest integration tests | PASS on Databricks |
| Intentional defects in seed data | 700 (manifest-verified) |
