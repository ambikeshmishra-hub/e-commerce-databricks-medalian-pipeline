# AI Prompts — Silver Layer

## Prompt 1: Completeness Quality Check

**PROMPT SENT:**
"@.cursorrules
Write `src/silver/01_quality_completeness.py` in PySpark.

Requirements:
1. Define `check_completeness(column_name: str, error_tag: str) -> Column`.
2. Use `pyspark.sql.functions.when()` to return `lit(error_tag)` when `col(column_name).isNull()`, otherwise `None`.
3. Do not drop rows. Use pure PySpark expressions without Python UDFs.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/01_quality_completeness.py` with:
```python
def check_completeness(column_name: str, error_tag: str) -> Column:
    return when(col(column_name).isNull(), lit(error_tag))
```
- Returns `error_tag` for null values; unmatched rows are null (no row drops)
- Pure PySpark `when` / `col` / `lit` — no UDFs
- `src/silver/__init__.py` re-exports `check_completeness` for `from src.silver import check_completeness`

Deployed and executed on Databricks:
- Module uploaded to `/Shared/medallion-pipeline/src/silver/`
- Notebook: `/Shared/medallion-pipeline/silver/01_quality_completeness`
- Validated against `workspace.bronze.bronze_customers` (NULL_EMAIL flags)
- Job submit via `conf/silver_01_quality_completeness_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/784666955523577/run/957658442366525

**YOUR EVALUATION:**
✓ **What was good:**
- Matches soft-quarantine pattern (expression-only, no row drops)
- Aligns with `.cursorrules` silver DQ design for building `dq_errors` arrays
- Notebook execution validates function against real bronze data

**FINAL DECISION:**
✅ **Accepted** — `check_completeness` ready for use in `create_silver_tables.py`.

---

## Prompt 2: Uniqueness Quality Check

**PROMPT SENT:**
"@.cursorrules
Write `src/silver/02_quality_uniqueness.py` in PySpark.

Requirements:
1. Define `flag_duplicates(df: DataFrame, id_col: str, count_col_name: str = "row_occurrence_count") -> DataFrame` using a PySpark Window partitioned by `id_col` to compute occurrence counts without grouping/dropping rows.
2. Define `check_uniqueness(count_col_name: str, error_tag: str) -> Column` returning `lit(error_tag)` when `col(count_col_name) > 1`.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/02_quality_uniqueness.py` with:
- `flag_duplicates()` — adds `row_occurrence_count` via `count(col(id_col)).over(Window.partitionBy(id_col))`
- `check_uniqueness()` — `when(col(count_col_name) > 1, lit(error_tag))`
- Exported from `src/silver/__init__.py`

Deployed and executed on Databricks:
- Module uploaded to `/Shared/medallion-pipeline/src/silver/`
- Notebook: `/Shared/medallion-pipeline/silver/02_quality_uniqueness`
- Validated against `workspace.bronze.bronze_customers` (`DUPLICATE_CUSTOMER_ID` flags)
- Job submit via `conf/silver_02_quality_uniqueness_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/1036647373117362/run/883781147530926

**YOUR EVALUATION:**
✓ **What was good:**
- Window-based duplicate detection preserves all rows (soft-quarantine compatible)
- Pure PySpark expressions, no UDFs

**FINAL DECISION:**
✅ **Accepted** — uniqueness helpers ready for silver pipeline integration.

---

## Prompt 3: Type Validation Quality Check

**PROMPT SENT:**
"@.cursorrules
Write `src/silver/03_quality_type_validation.py` in PySpark.

Requirements:
1. Define `check_numeric_positive(column_name: str, error_tag: str) -> Column`.
2. Return `lit(error_tag)` when `col(column_name) <= 0`, otherwise `None`.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/03_quality_type_validation.py` with:
```python
def check_numeric_positive(column_name: str, error_tag: str) -> Column:
    return when(col(column_name) <= 0, lit(error_tag))
```
- Exported from `src/silver/__init__.py`

Deployed and executed on Databricks:
- Module uploaded to `/Shared/medallion-pipeline/src/silver/`
- Notebook: `/Shared/medallion-pipeline/silver/03_quality_type_validation`
- Validated against `workspace.bronze.bronze_customers` (`NON_POSITIVE_LIFETIME_VALUE` flags)
- Job submit via `conf/silver_03_quality_type_validation_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/684863811996193/run/234685891409628

**YOUR EVALUATION:**
✓ **What was good:**
- Pure PySpark `when` expression, no UDFs, no row drops
- Validates intentional negative `lifetime_value` defects from generated data

**FINAL DECISION:**
✅ **Accepted** — `check_numeric_positive` ready for silver pipeline integration.

---

## Prompt 4: Referential Integrity Quality Check

**PROMPT SENT:**
"@.cursorrules
Write `src/silver/04_quality_referential_integrity.py` in PySpark.

Requirements:
1. Define `check_foreign_key(child_df: DataFrame, parent_df: DataFrame, fk_col: str, parent_pk_col: str, alias_col: str) -> DataFrame`.
2. Perform a LEFT OUTER JOIN against distinct parent primary keys so orphan records are retained for quarantine.
3. Define `flag_invalid_fk(alias_col: str, fk_col: str, error_tag: str) -> Column` returning `lit(error_tag)` when `col(fk_col).isNotNull() & col(alias_col).isNull()`.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/04_quality_referential_integrity.py` with:
- `check_foreign_key()` — left-joins child to `parent_df.select(parent_pk_col.alias(alias_col)).distinct()`
- `flag_invalid_fk()` — `when(col(fk_col).isNotNull() & col(alias_col).isNull(), lit(error_tag))`
- Exported from `src/silver/__init__.py`

Deployed and executed on Databricks:
- Module uploaded to `/Shared/medallion-pipeline/src/silver/`
- Notebook: `/Shared/medallion-pipeline/silver/04_quality_referential_integrity`
- Validated against `workspace.bronze.bronze_orders` joined to `workspace.bronze.bronze_customers` (`INVALID_CUSTOMER_ID_FK` flags)
- Job submit via `conf/silver_04_quality_referential_integrity_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/179635254485096/run/208032835315733

**YOUR EVALUATION:**
✓ **What was good:**
- LEFT OUTER JOIN preserves orphan rows for soft-quarantine
- `flag_invalid_fk` excludes NULL FKs (completeness handled separately)
- Pure PySpark expressions, no UDFs

**FINAL DECISION:**
✅ **Accepted** — referential integrity helpers ready for silver pipeline integration.

---

## Prompt 5: Business Logic Quality Check

**PROMPT SENT:**
"@.cursorrules
Write `src/silver/05_quality_business_logic.py` in PySpark.

Requirements:
1. Define `check_order_payment_dates(order_date_col: str, payment_date_col: str, error_tag: str) -> Column`.
2. Ensure that when `payment_date` is not null, it must be greater than or equal to `order_date`. Return `lit(error_tag)` if payment occurs before order date.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/05_quality_business_logic.py` with:
```python
def check_order_payment_dates(order_date_col, payment_date_col, error_tag) -> Column:
    return when(
        col(payment_date_col).isNotNull() & (col(payment_date_col) < col(order_date_col)),
        lit(error_tag),
    )
```
- Exported from `src/silver/__init__.py`

Deployed and executed on Databricks:
- Module uploaded to `/Shared/medallion-pipeline/src/silver/`
- Notebook: `/Shared/medallion-pipeline/silver/05_quality_business_logic`
- Validated against `workspace.bronze.bronze_orders` (`PAYMENT_BEFORE_ORDER_DATE` flags)
- Job submit via `conf/silver_05_quality_business_logic_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/178661853597393/run/487004887469904

**YOUR EVALUATION:**
✓ **What was good:**
- Only flags when `payment_date` is non-null and precedes `order_date`
- Pure PySpark `when` expression, no UDFs, no row drops

**FINAL DECISION:**
✅ **Accepted** — `check_order_payment_dates` ready for silver pipeline integration.

---

## Prompt 6: Create Silver Tables

**PROMPT SENT:**
"@spec.md @.cursorrules @src/silver/
Write `src/silver/create_silver_tables.py` in PySpark.

Requirements:
1. Read tables `bronze_orders`, `bronze_customers`, and `bronze_products`.
2. Apply the modular DQ checks imported from `src.silver.01` through `src.silver.05`.
3. Combine all check outputs into an array column `dq_errors` using `array()` and `array_remove(..., None)`.
4. Add column `quality_check_result`: assign 'PASS' if `size(col("dq_errors")) == 0`, otherwise 'FAIL'.
5. Drop temporary lookup columns and save the result as Delta table `silver_orders`.
6. Calculate and print a Data Quality Metrics Summary to stdout showing total rows processed, passed rows (count and %), and quarantined bad rows (count and %).
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/silver/create_silver_tables.py` orchestrating all five DQ modules on bronze orders:
- Completeness: `NULL_CUSTOMER_ID`, `NULL_PRODUCT_ID`
- Uniqueness: `DUPLICATE_ORDER_ID` via `flag_duplicates` + `check_uniqueness`
- Type validation: `NON_POSITIVE_QUANTITY`, `NON_POSITIVE_UNIT_PRICE`, `NON_POSITIVE_TOTAL_AMOUNT`
- Referential integrity: `INVALID_CUSTOMER_ID_FK`, `INVALID_PRODUCT_ID_FK` via LEFT OUTER JOINs to bronze customers/products
- Business logic: `PAYMENT_BEFORE_ORDER_DATE`
- `dq_errors` built with `array_remove(array(...), None)`; `quality_check_result` PASS/FAIL from `size(dq_errors)`
- Drops temp columns (`row_occurrence_count`, `matched_customer_id`, `matched_product_id`)
- Writes `workspace.silver.silver_orders` and prints DQ metrics summary

Deployed and executed on Databricks:
- Notebook: `/Shared/medallion-pipeline/silver/create_silver_tables`
- Job submit via `conf/silver_create_silver_tables_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/678324521440307/run/683484383485138

**YOUR EVALUATION:**
✓ **What was good:**
- Integrates all modular DQ helpers without dropping rows (soft-quarantine)
- LEFT OUTER JOIN FK pattern preserves orphan records
- Metrics summary printed to stdout

**FINAL DECISION:**
✅ **Accepted** — `workspace.silver.silver_orders` created with full DQ soft-quarantine pipeline.
