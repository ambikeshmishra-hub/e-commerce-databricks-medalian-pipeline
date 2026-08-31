# Design Notes — E-Commerce Medallion Pipeline

## 1. High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  CSV Sources    │────▶│  Bronze Layer    │────▶│  Silver Layer   │────▶│  Gold Layer  │
│  (UC Volume)    │     │  Lossless Ingest │     │  Soft Quarantine│     │  PASS-only   │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
        │                        │                        │                      │
   customers.csv            bronze_customers          silver_orders         gold_sales_by_product
   orders.csv              bronze_orders             (dq_errors,           gold_revenue_by_customer
   products.csv            bronze_products            quality_check_result) gold_daily_weekly_trends
                                                                               gold_customer_segmentation
                                                                                      │
                                                                                      ▼
                                                                              ┌──────────────┐
                                                                              │  Dashboard   │
                                                                              │  SQL Tiles   │
                                                                              └──────────────┘
```

### Design Principles

1. **Separation of concerns** — each layer has a single responsibility.
2. **Fail-safe, not fail-silent** — bad data is flagged, never hidden.
3. **Modular DQ** — five independent check modules compose into one orchestrator.
4. **Dual execution** — Python modules run locally (unit tests) and on Databricks (notebooks + serverless jobs).

---

## 2. Data Models & Schema Flow

| Layer | Tables | Grain | Key Additions |
|---|---|---|---|
| **Source** | CSV files | Entity-native | None |
| **Bronze** | `bronze_customers`, `bronze_orders`, `bronze_products` | Same as CSV | `_ingested_at`, `_source_file` |
| **Silver** | `silver_orders` | Order line | `dq_errors`, `quality_check_result` |
| **Gold** | 4 mart tables | Aggregated | Business metrics only |

**Schema evolution path:**

- Bronze preserves raw types as inferred by Spark CSV reader (strings that look numeric become numeric; dirty values like `"N/A"` remain strings).
- Silver adds DQ columns but does not coerce source columns.
- Gold reads silver facts + bronze dimensions for descriptive attributes.

---

## 3. Bronze Layer Design

### 3.1 Lossless Ingestion

Bronze ingestion reads CSV with:

```python
spark.read.option("header", "true").option("inferSchema", "true").csv(source_path)
```

No `dropna()`, no `filter()`, no `distinct()`—every row in the file lands in Delta.

### 3.2 Metadata Columns

| Column | Type | Source | Purpose |
|---|---|---|---|
| `_ingested_at` | TIMESTAMP | `current_timestamp()` | When the row was ingested |
| `_source_file` | STRING | `_metadata.file_path` | Lineage to source file path |

**Design decision:** On Unity Catalog volumes, `input_file_name()` is unreliable. `_metadata.file_path` is the CE-compatible alternative discovered during debugging.

### 3.3 Write Pattern

```python
bronze_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(...)
```

- **Overwrite** for idempotent dev runs.
- **overwriteSchema** handles column additions during iteration.

### 3.4 Module Structure

| Module | Responsibility |
|---|---|
| `databricks_ingest.py` | CE-compatible ingest functions |
| `01_ingest_customers.py` | Local + importable customer ingest |
| `02_ingest_orders.py` | Order ingest |
| `03_ingest_products.py` | Product ingest |
| `ingest_all.py` | Sequential orchestration |
| `*_nb.py` | Databricks notebook entry points |

---

## 4. Silver Layer Design

### 4.1 Soft Quarantine Model

```
For each bronze_orders row:
  1. Compute dq_errors[] = [rule1, rule2, ..., ruleN]  (nulls filtered out)
  2. quality_check_result = PASS if len(dq_errors) == 0 else FAIL
  3. Write row to silver_orders (always)
```

**Invariant:** `count(bronze_orders) == count(silver_orders)` — enforced by integration tests.

### 4.2 DQ Column Schema

| Column | Type | Description |
|---|---|---|
| `dq_errors` | `ARRAY<STRING>` | Error tags for failed rules (empty array on PASS) |
| `quality_check_result` | `STRING` | `'PASS'` or `'FAIL'` |

### 4.3 Modular Check Pipeline

Execution order in `create_silver_tables.py`:

```
bronze_orders
  → flag_duplicates(order_id)           # Uniqueness prep
  → check_foreign_key(customers)        # LEFT JOIN → matched_customer_id
  → check_foreign_key(products)        # LEFT JOIN → matched_product_id
  → build dq_errors array:
      - check_completeness(customer_id)
      - check_completeness(product_id)
      - check_uniqueness(row_occurrence_count)
      - check_numeric_positive(quantity, unit_price, total_amount)
      - flag_invalid_fk(matched_customer_id)
      - flag_invalid_fk(matched_product_id)
      - check_order_payment_dates(order_date, payment_date)
  → set quality_check_result
  → drop temp columns
  → write silver_orders
```

### 4.4 array_filter vs. array_remove

**Bug discovered:** `array_remove(dq_errors, None)` on Databricks marked **all rows as FAIL** because null-sentinel handling differed from local Spark.

**Fix:** `array_filter(array(...), lambda x: x.isNotNull())` — explicit null filtering compatible with Catalyst.

### 4.5 Referential Integrity — LEFT OUTER JOIN Pattern

```python
parent_keys = parent_df.select(col(parent_pk_col).alias(alias_col)).distinct()
return child_df.join(parent_keys, col(fk_col) == col(alias_col), "left")
```

**Why not INNER JOIN?** INNER JOIN drops orphan FK rows before DQ tagging, making it impossible to quarantine them and causing bronze/silver row-count mismatch.

**Pre-join renaming:** Parent PK aliased to `matched_customer_id` / `matched_product_id` to avoid ambiguous column names after join.

---

## 5. Gold Layer Design

### 5.1 PASS-Only Sourcing

Every gold SQL file includes:

```sql
WHERE o.quality_check_result = 'PASS'
```

This is the **only** place bad rows are excluded from analytics.

### 5.2 Mart Definitions

| Table | Grain | Key Metrics |
|---|---|---|
| `gold_sales_by_product` | Product | `total_orders`, `total_revenue`, `avg_order_value` |
| `gold_revenue_by_customer` | Customer | `total_orders`, `total_revenue`, `avg_order_value`, `lifetime_value_actual` |
| `gold_daily_weekly_trends` | Day + Week | `daily_order_count`, `daily_revenue` |
| `gold_customer_segmentation` | Segment type | `customer_count`, `avg_revenue`, `total_revenue` |

### 5.3 Dimension Joins in Gold

Gold joins silver facts to **bronze** dimension tables (not silver dimensions) because only `silver_orders` exists. In production, silver dimensions would be preferred once built.

### 5.4 Orchestration

`create_gold_tables.py` executes four SQL files sequentially via `spark.sql()`.

---

## 6. Data Quality Validation Strategy

### 6.1 Check Categories

| Module | File | Functions | Error Tags |
|---|---|---|---|
| Completeness | `01_quality_completeness.py` | `check_completeness()` | `NULL_CUSTOMER_ID`, `NULL_PRODUCT_ID` |
| Uniqueness | `02_quality_uniqueness.py` | `flag_duplicates()`, `check_uniqueness()` | `DUPLICATE_ORDER_ID` |
| Type Validation | `03_quality_type_validation.py` | `check_numeric_positive()` | `NON_POSITIVE_*` |
| Referential Integrity | `04_quality_referential_integrity.py` | `check_foreign_key()`, `flag_invalid_fk()` | `INVALID_*_FK` |
| Business Logic | `05_quality_business_logic.py` | `check_order_payment_dates()` | `PAYMENT_BEFORE_ORDER_DATE` |

### 6.2 Threshold Targets

| Metric | Target |
|---|---|
| Completeness (non-null FK fields) | > 99% |
| Uniqueness (`order_id`) | 100% unique among PASS rows |
| FK validity | > 99.9% |
| Overall PASS rate (orders) | > 98% (after 700 injected defects, ~99.2% observed) |

### 6.3 Metrics Reporting

`print_dq_metrics_summary()` outputs:

```
============================================================
Data Quality Metrics Summary — silver_orders
============================================================
Total rows processed:          50,000
Passed rows:                   49,xxx ( xx.xx%)
Quarantined bad rows:             xxx (  x.xx%)
============================================================
```

---

## 7. Debugging Approach

### 7.1 Documented Issues (`database/debugging-notes.md`)

| Issue | Root Cause | Fix |
|---|---|---|
| DBFS 403 | CE FileStore restrictions | UC volume `workspace.default.medallion_data` |
| `input_file_name()` empty | UC volume incompatibility | `_metadata.file_path` |
| All silver rows FAIL | `array_remove` null bug | `array_filter` with lambda |
| ANSI cast exception | `"N/A"` quantity string | `try_cast(... AS DOUBLE)` |
| Ambiguous `customer_id` | Join column collision | Alias parent keys before join |
| Gold empty | Silver all FAIL (above bugs) | Fixed silver; gold repopulated |

### 7.2 Debugging Workflow

1. **Row-count parity check** — bronze vs. silver first.
2. **Sample FAIL rows** — `SELECT order_id, dq_errors FROM silver_orders WHERE quality_check_result = 'FAIL' LIMIT 20`.
3. **Rule isolation** — unit tests in `test_silver_rules.py` per helper function.
4. **Integration gate** — `test_pipeline.py` on Databricks before declaring layer complete.

### 7.3 Eliminating UDFs

All DQ helpers return `Column` expressions using `when()`, `col()`, `lit()`, `expr()`. This ensures:

- Catalyst can optimize predicate pushdown.
- No Python worker serialization per row.
- Functions are unit-testable by building small DataFrames and checking output columns.

---

## 8. Deployment Architecture

```
Local Dev                    Databricks CE
─────────                    ─────────────
generate_sample_data.py  →   Upload CSVs to UC volume
src/**/*.py              →   Import to /Shared/medallion-pipeline/
conf/*_run.json          →   databricks jobs submit --json @conf/...
tests/*.py               →   Serverless pytest execution
```

Job configs use `environment_version: 3` for serverless compute.

---

## 9. Future Design Considerations

| Area | Recommendation |
|---|---|
| Orchestration | Migrate to Delta Live Tables with `EXPECT` constraints |
| DQ framework | Integrate Great Expectations checkpoint suites |
| Silver scope | Add `silver_customers`, `silver_products` |
| Incremental | Bronze append + `merge` instead of overwrite |
| Partitioning | Partition bronze/silver by `order_date` for large volumes |
