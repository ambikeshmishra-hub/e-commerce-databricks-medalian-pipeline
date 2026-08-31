# Debugging Notes

Troubleshooting log for real issues encountered while building and validating the Medallion pipeline on Databricks Community Edition.

---

## Issue 1: Ambiguous `customer_id` During Silver Parent-Child Joins

### Symptom

```
AnalysisException: Reference 'customer_id' is ambiguous
```

Occurred when joining `bronze_orders` to `bronze_customers` during referential integrity checks in the Silver layer. Both DataFrames contained a `customer_id` column, and subsequent `select()` / `withColumn()` expressions could not resolve which table the reference belonged to.

### Root Cause

A naive join pattern kept both sides of the join key under the same column name:

```python
# Problematic pattern
child_df.join(parent_df, on="customer_id", how="left")
```

After the join, Spark sees two `customer_id` columns (or an unresolvable self-reference in downstream expressions).

### Fix

Renamed parent primary keys **before** the join using a dedicated alias column, as implemented in `src/silver/04_quality_referential_integrity.py`:

```python
parent_keys = parent_df.select(col(parent_pk_col).alias(alias_col)).distinct()
return child_df.join(parent_keys, col(fk_col) == col(alias_col), "left")
```

The child retains `customer_id`; the parent match is exposed as `matched_customer_id`. `flag_invalid_fk()` then references the alias explicitly:

```python
when(col(fk_col).isNotNull() & col(alias_col).isNull(), lit(error_tag))
```

### Prevention

- Always alias parent keys to a distinct column name (`matched_*`) before joining
- Drop temporary lookup columns (`matched_customer_id`, `matched_product_id`) after building `dq_errors`
- Codified in `.cursorrules`: use **LEFT OUTER JOIN** (not INNER JOIN) to preserve orphan rows

### Files Affected

- `src/silver/04_quality_referential_integrity.py`
- `src/silver/create_silver_tables.py`

---

## Issue 2: Future Signup Dates in Synthetic Customer Generation

### Symptom

Orders generated for customers with **future `signup_date`** values produced unrealistic `order_date` sequences (orders appearing before plausible customer lifecycle windows). During exploratory analysis, date histograms showed order dates clustering oddly for a subset of customers.

### Root Cause

The data generator intentionally injects future signup defects (`IssueSpec C05` — 10 rows with `signup_date = 2027-01-01`) for Silver-layer DQ testing. However, the baseline Faker date range for **non-defect** rows could also drift forward if `SIGNUP_END` was set beyond the assessment date, and the orders generator used `signup_date` directly as the lower bound for `order_date`:

```python
order_start = signup_date  # problematic when signup_date > ORDER_END
```

### Fix

1. **Bounded baseline generation ranges** with fixed upper limits (`SIGNUP_END = date(2024, 12, 31)`, `ORDER_END = date(2025, 12, 31)`) so non-defect rows stay within realistic windows.

2. **Guarded order date generation** when lookup signup is in the future (intentional defect rows):

```python
order_start = signup_date if signup_date <= ORDER_END else ORDER_START
```

3. Retained intentional future-date defects in the manifest for DQ validation — they are now isolated anomalies rather than systemic generation artifacts.

### Prevention

- Separate **baseline realism** from **intentional defect injection** in the generator
- Document defect rows in `ISSUE_MANIFEST` so debugging distinguishes expected vs. accidental anomalies

### Files Affected

- `src/data_generation/generate_sample_data.py`

---

## Issue 3: Schema Evolution Mismatch Writing Delta Tables

### Symptom

```
AnalysisException: A schema mismatch detected when writing to the Delta table
```

Occurred when re-running bronze ingestion after CSV schema changes (e.g., `inferSchema` producing different column types between runs — `quantity` shifting from `INT` to `STRING` after injecting `"N/A"` values).

### Root Cause

Delta Lake enforces **schema compatibility** on append/overwrite by default. When the inferred CSV schema changed between pipeline runs, `saveAsTable()` rejected the write because existing table columns had incompatible types.

### Fix

Added `overwriteSchema` to all Delta write operations:

```python
(
    bronze_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("workspace.bronze.bronze_orders")
)
```

Applied consistently across:

- `src/bronze/01_ingest_customers.py` (and orders/products variants)
- `src/bronze/databricks_ingest.py`
- `src/silver/create_silver_tables.py`
- Databricks notebook variants (`*_nb.py`)

### Prevention

- Use `overwriteSchema=true` for development/assessment pipelines with evolving schemas
- In production, prefer explicit `StructType` schemas instead of `inferSchema=true` to avoid type drift
- Run `spark.table(...).printSchema()` after ingest to verify column types

### Files Affected

- All bronze ingest modules and `create_silver_tables.py`

---

## Additional Issues (Discovered During Integration Testing)

| Issue | Symptom | Fix |
|---|---|---|
| `array_remove(..., None)` on Databricks | All 50,000 silver rows marked `FAIL` with empty-looking `dq_errors` | Replaced with `array_filter(..., lambda x: x.isNotNull())` |
| ANSI `try_cast` | `CAST_INVALID_INPUT` on `quantity = 'N/A'` | `check_numeric_positive` uses `try_cast(... AS DOUBLE)` |
| UC `input_file_name()` | Not supported on Unity Catalog volumes | Switched to `F.col("_metadata.file_path")` in `*_nb.py` |
| DBFS FileStore 403 | Cannot upload to `dbfs:/FileStore/...` on CE | Migrated to UC volume `workspace.default.medallion_data` |

See `ai-prompts/debugging.md` and `tests/test_pipeline.py` for validation details.
