# AI Prompts — Bronze Layer

## Prompt 1: Ingest Customers Bronze Script

**PROMPT SENT:**
"@spec.md @.cursorrules
Write `src/bronze/01_ingest_customers.py` using PySpark.

Requirements:
1. Define `ingest_customers(spark: SparkSession, source_path: str = "data/customers.csv")`.
2. Read the CSV using `header=True` and `inferSchema=True`.
3. Add audit metadata columns:
   - `_ingested_at` using `current_timestamp()`
   - `_source_file` using `input_file_name()`
4. Save the DataFrame as a Delta table named `bronze_customers` with mode="overwrite" and option("overwriteSchema", "true").
5. Include an `if __name__ == "__main__":` block to initialize a SparkSession with Delta Lake extensions for standalone testing."

**AI RESPONSE SUMMARY:**
Created `src/bronze/01_ingest_customers.py` with:
- `ingest_customers(spark, source_path="data/customers.csv")` reading CSV with `header=True` and `inferSchema=True`
- Metadata columns `_ingested_at` (`F.current_timestamp()`) and `_source_file` (`F.input_file_name()`)
- Delta write to `bronze_customers` with `mode("overwrite")` and `option("overwriteSchema", "true")`
- `if __name__ == "__main__":` block using `_build_spark_session()` with Delta Lake session extensions
- Relative `data/customers.csv` paths resolved from project root for local standalone runs

**YOUR EVALUATION:**
✓ **What was good:**
- Matches spec customer schema ingestion path and `.cursorrules` bronze metadata requirements
- Native PySpark functions only (no UDFs); type hints and docstrings included
- Reusable function signature for notebook/job orchestration

△ **Missing:**
- Standalone run requires Delta Lake JARs on the local Spark classpath (typically run on Databricks)

**FINAL DECISION:**
✅ **Accepted** — ready for Databricks execution against `data/customers.csv`.

---

## Prompt 2: Push Notebook to Databricks & Execute

**PROMPT SENT:**
"push the code to a databricks notebook and execute"

**AI RESPONSE SUMMARY:**
- Uploaded `data/customers.csv` → `dbfs:/Volumes/workspace/default/medallion_data/customers.csv`
- Imported notebook → `/Shared/medallion-pipeline/bronze/01_ingest_customers`
- Executed via serverless `jobs submit` (`conf/bronze_ingest_customers_run.json`) — **SUCCESS**
- Created Delta table: `workspace.bronze.bronze_customers`
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/114873378429020/run/947000185745719

**Note:** Unity Catalog on Community Edition does not support `input_file_name()`; notebook uses `F.col("_metadata.file_path")` for `_source_file` instead (local `01_ingest_customers.py` unchanged per original spec).

**YOUR EVALUATION:**
✓ **What was good:**
- Notebook deployed and executed successfully on serverless compute
- Bronze schema/table created in `workspace.bronze`
- CSV source available in UC volume for pipeline runs

✗ **What needed fixing:**
- First run failed on UC `input_file_name()` — fixed in notebook variant `01_ingest_customers_nb.py`

**FINAL DECISION:**
✅ **Accepted** — `workspace.bronze.bronze_customers` is live in Databricks.

---

## Prompt 3: Ingest Orders Bronze Script + Databricks Execute

**PROMPT SENT:**
"@spec.md @.cursorrules
Write `src/bronze/02_ingest_orders.py` using PySpark.

Requirements:
1. Define `ingest_orders(spark: SparkSession, source_path: str = "data/orders.csv")`.
2. Read CSV with header and inferred schema.
3. Append `_ingested_at` and `_source_file` metadata columns.
4. Overwrite-save to Delta table `bronze_orders`.
5. Include the standalone execution entry point under `__main__`.

push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/bronze/02_ingest_orders.py` mirroring the customers ingest pattern:
- `ingest_orders(spark, source_path="data/orders.csv")` with `header=True`, `inferSchema=True`
- Metadata: `_ingested_at` (`F.current_timestamp()`), `_source_file` (`F.input_file_name()` locally)
- Delta overwrite to `bronze_orders` with `overwriteSchema=true`
- `if __name__ == "__main__":` standalone entry point

Deployed and executed on Databricks:
- Uploaded `data/orders.csv` → `dbfs:/Volumes/workspace/default/medallion_data/orders.csv`
- Notebook: `/Shared/medallion-pipeline/bronze/02_ingest_orders` (`02_ingest_orders_nb.py` uses `_metadata.file_path` for UC)
- Job submit via `conf/bronze_ingest_orders_run.json` — **SUCCESS**
- Delta table: `workspace.bronze.bronze_orders`
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/466543168077743/run/592393679599334

**YOUR EVALUATION:**
✓ **What was good:**
- Matches spec orders schema and bronze metadata rules
- First-run success on serverless (UC-compatible notebook variant)
- Consistent pattern with `01_ingest_customers`

**FINAL DECISION:**
✅ **Accepted** — `workspace.bronze.bronze_orders` is live in Databricks.

---

## Prompt 4: Ingest Products Bronze Script + Databricks Execute

**PROMPT SENT:**
"@spec.md @.cursorrules
Write `src/bronze/03_ingest_products.py` using PySpark.

Requirements:
1. Define `ingest_products(spark: SparkSession, source_path: str = "data/products.csv")`.
2. Read CSV with header and inferred schema.
3. Append `_ingested_at` and `_source_file` metadata columns.
4. Overwrite-save to Delta table `bronze_products`.
5. Include the standalone execution entry point under `__main__`.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created `src/bronze/03_ingest_products.py` mirroring the customers/orders ingest pattern:
- `ingest_products(spark, source_path="data/products.csv")` with `header=True`, `inferSchema=True`
- Metadata: `_ingested_at` (`F.current_timestamp()`), `_source_file` (`F.input_file_name()` locally)
- Delta overwrite to `bronze_products` with `overwriteSchema=true`
- `if __name__ == "__main__":` standalone entry point

Deployed and executed on Databricks:
- Uploaded `data/products.csv` → `dbfs:/Volumes/workspace/default/medallion_data/products.csv`
- Notebook: `/Shared/medallion-pipeline/bronze/03_ingest_products` (`03_ingest_products_nb.py` uses `_metadata.file_path` for UC)
- Job submit via `conf/bronze_ingest_products_run.json` — **SUCCESS**
- Delta table: `workspace.bronze.bronze_products`
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/8455397344382/run/1024337633899276

**YOUR EVALUATION:**
✓ **What was good:**
- Matches spec products schema and bronze metadata rules
- First-run success on serverless compute
- Bronze layer now complete: `bronze_customers`, `bronze_orders`, `bronze_products`

**FINAL DECISION:**
✅ **Accepted** — `workspace.bronze.bronze_products` is live in Databricks.

---

## Prompt 5: Ingest All Bronze Orchestrator + Databricks Execute

**PROMPT SENT:**
"@spec.md @.cursorrules
Write `src/bronze/ingest_all.py` using PySpark.

Requirements:
1. Import `ingest_customers`, `ingest_orders`, and `ingest_products` from `src.bronze`.
2. Initialize a single shared SparkSession with Delta Lake catalog support.
3. Execute all three ingestion functions sequentially.
4. Log progress and record counts to the console for pipeline observability.
push the code to databricks on notebook & execute it"

**AI RESPONSE SUMMARY:**
Created bronze orchestration package:
- `src/bronze/__init__.py` — exports `ingest_customers`, `ingest_orders`, `ingest_products` (local modules via importlib; Databricks UC modules via `databricks_ingest.py`)
- `src/bronze/ingest_all.py` — `run_bronze_ingestion(spark)` runs all three ingestions sequentially with console logging and row counts
- `src/bronze/databricks_ingest.py` — UC-compatible ingest functions for Community Edition
- `src/bronze/ingest_all_nb.py` — Databricks notebook orchestrator

Deployed and executed:
- Uploaded package files to `/Shared/medallion-pipeline/src/`
- Notebook: `/Shared/medallion-pipeline/bronze/ingest_all`
- Job submit via `conf/bronze_ingest_all_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/132975143343519/run/787833135800844

**YOUR EVALUATION:**
✓ **What was good:**
- Single shared SparkSession on Databricks (`spark`); local `__main__` uses Delta-enabled session
- Sequential pipeline with per-dataset progress and row-count logging
- Imports from `src.bronze` as required

**FINAL DECISION:**
✅ **Accepted** — full bronze pipeline orchestrator live on Databricks.
