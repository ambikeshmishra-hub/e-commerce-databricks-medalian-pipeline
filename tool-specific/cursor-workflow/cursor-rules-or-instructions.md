# Cursor Rules & Instructions — Workspace Standards

Comprehensive documentation of all workspace rules, coding standards, and engineering practices governing the Databricks Medallion pipeline project.

---

## 1. Platform & Runtime

| Requirement | Standard |
|---|---|
| **Platform** | Databricks / Delta Lake |
| **Spark** | PySpark 3.4+ |
| **Python** | 3.10+ (local dev); 3.9+ on CE serverless |
| **Catalog** | Unity Catalog (`workspace` catalog) |
| **Schemas** | `workspace.bronze`, `workspace.silver`, `workspace.gold` |
| **Source data** | UC volume `dbfs:/Volumes/workspace/default/medallion_data/` |
| **Deployment** | `/Shared/medallion-pipeline/` workspace path |

---

## 2. Medallion Architecture Rules

### 2.1 Bronze Layer

| Rule | Description |
|---|---|
| **BR-LOSSLESS** | Ingest raw CSV data with zero row or column loss |
| **BR-META** | Append `_ingested_at` (TIMESTAMP) and `_source_file` (STRING) to every row |
| **BR-LINEAGE** | Use `_metadata.file_path` for source file path on UC volumes |
| **BR-DELTA** | Write to Delta tables with `overwrite` + `overwriteSchema` for dev idempotency |
| **BR-NO-FILTER** | No `filter()`, `dropna()`, or `distinct()` during ingest |

### 2.2 Silver Layer

| Rule | Description |
|---|---|
| **SV-QUARANTINE** | Soft quarantine: flag bad rows, never drop them |
| **SV-DQ-ERRORS** | `dq_errors ARRAY<STRING>` — one or more error tags per failed rule |
| **SV-RESULT** | `quality_check_result STRING` — `'PASS'` if `size(dq_errors) = 0`, else `'FAIL'` |
| **SV-PARITY** | `count(silver_orders) == count(bronze_orders)` — enforced by tests |
| **SV-LEFT-JOIN** | Referential integrity checks use **LEFT OUTER JOIN** only |
| **SV-ALIAS** | Pre-join rename parent PK to alias (`matched_customer_id`) to avoid ambiguity |
| **SV-CLEANUP** | Drop temporary columns (`row_occurrence_count`, `matched_*`) before write |
| **SV-ARRAY** | Use `array_filter(..., lambda x: x.isNotNull())` — not `array_remove(..., None)` |

### 2.3 Gold Layer

| Rule | Description |
|---|---|
| **GD-PASS-ONLY** | Source only rows where `quality_check_result = 'PASS'` |
| **GD-SQL** | Aggregations in SQL files executed by Python orchestrator |
| **GD-ROUND** | Monetary values rounded to 2 decimal places |
| **GD-NO-DQ** | Gold does not re-validate DQ — trusts silver flags |

---

## 3. PySpark Coding Standards

### 3.1 No Python UDFs

```python
# ✗ FORBIDDEN
from pyspark.sql.functions import udf
@udf("string")
def my_check(val): ...

# ✓ REQUIRED
from pyspark.sql.functions import when, col, lit
when(col("customer_id").isNull(), lit("NULL_CUSTOMER_ID"))
```

**Rationale:** UDFs bypass Catalyst optimizer, serialize Python per row, and degrade performance at scale.

### 3.2 Vectorized Operations Only

All DQ rules return `pyspark.sql.Column` expressions composable via:

- `when()` / `otherwise()`
- `col()` / `lit()`
- `expr()` for `try_cast` and SQL fragments
- `array()` / `array_filter()` for error aggregation
- `size()` for array length checks

### 3.3 Window-Based Deduplication (Not dropDuplicates)

```python
# ✓ CORRECT — preserves all rows, adds count column
duplicate_window = Window.partitionBy("order_id")
df.withColumn("row_occurrence_count", count(col("order_id")).over(duplicate_window))

# ✗ FORBIDDEN — silently drops rows
df.dropDuplicates(["order_id"])
```

### 3.4 LEFT OUTER JOIN for Referential Integrity

```python
# ✓ CORRECT — orphan rows preserved
child_df.join(parent_keys, col(fk_col) == col(alias_col), "left")

# ✗ FORBIDDEN — orphan rows silently dropped
child_df.join(parent_keys, col(fk_col) == col(parent_pk_col), "inner")
```

### 3.5 Safe Type Casting

```python
# ✓ CORRECT — no ANSI exception on dirty strings
expr(f"try_cast(`{column_name}` AS DOUBLE)")

# ✗ RISKY — throws on "N/A" strings in ANSI mode
col(column_name).cast("double")
```

### 3.6 Avoid collect() on Large Datasets

```python
# ✗ AVOID on production-scale data
df.collect()

# ✓ USE aggregations
df.agg(count(lit(1)).alias("total")).first()
df.filter(...).count()
```

### 3.7 Type Hints & Docstrings

- All functions must have PEP-257 docstrings with Args/Returns sections.
- Use `from __future__ import annotations` for forward-compatible type hints.
- Prefer `DataFrame`, `Column`, `SparkSession` type annotations.

---

## 4. Module Organization

### 4.1 Directory Structure

```
src/
├── bronze/          # Lossless CSV ingest
├── silver/          # Modular DQ checks + orchestrator
├── gold/            # SQL marts + orchestrator
├── dashboard/       # BI queries + guide
└── data_generation/ # Synthetic CSV generator
```

### 4.2 Naming Conventions

| Pattern | Example |
|---|---|
| Numbered modules | `01_quality_completeness.py` |
| Notebook wrappers | `01_quality_completeness_nb.py` |
| Job configs | `conf/silver_01_quality_completeness_run.json` |
| Delta tables | `bronze_orders`, `silver_orders`, `gold_sales_by_product` |
| DQ error tags | `SCREAMING_SNAKE_CASE` (e.g., `NULL_CUSTOMER_ID`) |

### 4.3 Dual Execution Pattern

Every pipeline module has:

1. **Python module** — importable, testable locally
2. **Notebook wrapper** (`*_nb.py`) — Databricks entry point with `sys.path` setup
3. **Job JSON** (`conf/*_run.json`) — serverless execution config

---

## 5. Data Quality Function API

All silver DQ helpers follow a consistent signature:

| Function | Returns | Pattern |
|---|---|---|
| `check_completeness(col, tag)` | `Column` | `when(col.isNull(), lit(tag))` |
| `check_uniqueness(count_col, tag)` | `Column` | `when(count_col > 1, lit(tag))` |
| `check_numeric_positive(col, tag)` | `Column` | `when(try_cast <= 0, lit(tag))` |
| `flag_invalid_fk(alias, fk, tag)` | `Column` | `when(fk.notNull() & alias.isNull(), lit(tag))` |
| `check_order_payment_dates(...)` | `Column` | `when(payment < order, lit(tag))` |
| `flag_duplicates(df, id_col)` | `DataFrame` | Window count column |
| `check_foreign_key(child, parent, ...)` | `DataFrame` | LEFT JOIN with alias |

---

## 6. Testing Standards

| Rule | Description |
|---|---|
| **TS-INTEGRATION** | `test_pipeline.py` validates bronze counts, silver parity, gold integrity |
| **TS-UNIT** | `test_silver_rules.py` tests individual DQ helpers |
| **TS-THRESHOLD** | `MIN_QUARANTINED_ROWS = 400` for anomaly detection |
| **TS-DATABRICKS** | Integration tests run on Databricks via serverless jobs |
| **TS-NOTEBOOK** | `test_pipeline_nb.py` refreshes silver+gold before testing |

---

## 7. Deployment Standards

### 7.1 Workspace Import

```bash
databricks workspace import /Shared/medallion-pipeline/src/bronze/01_ingest_customers_nb.py \
  --file src/bronze/01_ingest_customers_nb.py --format SOURCE --overwrite --profile community
```

### 7.2 Job Execution

```bash
databricks jobs submit --json @conf/bronze_ingest_all_run.json --profile community --timeout 30m
```

### 7.3 Notebook Path Setup

```python
import sys
sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")
```

---

## 8. Security Standards

| Rule | Description |
|---|---|
| **SEC-NO-SECRETS** | Never commit tokens, passwords, or API keys |
| **SEC-PROFILE** | Use `~/.databrickscfg` with named profiles |
| **SEC-EXAMPLE** | `conf/databrickscfg.example` provides template only |
| **SEC-SYNTHETIC** | Faker-generated data only — no real PII |
| **SEC-NO-EVAL** | No `eval()` or unsafe deserialization |

---

## 9. AI Prompt Logging Rules

| Rule | Description |
|---|---|
| **LOG-APPEND** | Append each user prompt verbatim to `ai-prompts/<topic>.md` |
| **LOG-FORMAT** | `## Prompt N:` → **PROMPT SENT:** → **AI RESPONSE SUMMARY:** → **YOUR EVALUATION:** |
| **LOG-TOPIC** | Map by layer: bronze → `bronze-layer.md`, silver → `silver-layer.md`, etc. |
| **LOG-NO-META** | Do not log meta-instructions or prompt-logging rules themselves |
| **LOG-EVAL** | Mark ✓ good / ✗ fixes / △ missing |

---

## 10. Git & Branch Standards

| Rule | Description |
|---|---|
| **GIT-BRANCH** | Cloud agents work on `cursor/<ticket>-<summary>` branches |
| **GIT-NO-MAIN** | Never push directly to main or release branches |
| **GIT-COMMIT** | Only commit when explicitly requested |

---

## 11. Dependency Discipline

| Rule | Description |
|---|---|
| **DEP-MINIMAL** | No new dependencies unless necessary |
| **DEP-PIN** | Pin versions in `requirements.txt` |
| **DEP-JUSTIFY** | Document why a new library is needed |

Current dependencies: `pyspark`, `delta-spark`, `pandas`, `numpy`, `faker`, `pytest`, `databricks-cli`.

---

## 12. Code Review Checklist

Before accepting AI-generated pipeline code:

- [ ] No `@udf` decorators
- [ ] No `INNER JOIN` for FK validation
- [ ] No `dropDuplicates()` or row-filtering in silver
- [ ] Bronze has `_ingested_at` and `_source_file`
- [ ] Silver has `dq_errors` and `quality_check_result`
- [ ] Gold SQL has `WHERE quality_check_result = 'PASS'`
- [ ] Type hints and docstrings present
- [ ] Tests updated if behavior changed
- [ ] Prompt logged to `ai-prompts/`
