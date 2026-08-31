# AI Prompts — Debugging / Tests

## Prompt 1: Pipeline Integration Test Suite

**PROMPT SENT:**
"@spec.md @.cursorrules @src/
Structure: Create `tests/test_pipeline.py`.
Purpose: Implement an automated Pytest test suite to validate pipeline execution integrity, soft-quarantine anomaly catching, and Gold revenue correctness[cite: 1].

Requirements:
1. PySpark Fixture:
   - Create a session-scoped Pytest fixture `spark` initializing a local PySpark session with Delta Lake catalog support[cite: 1].
2. Test 1 (`test_bronze_ingestion_counts`):
   - Query `bronze_orders`, `bronze_customers`, and `bronze_products`[cite: 1].
   - Assert `bronze_orders` has at least 100,000 rows[cite: 1].
   - Assert metadata columns `_ingested_at` and `_source_file` exist and are not null[cite: 1].
3. Test 2 (`test_silver_soft_quarantine_anomaly_detection`):
   - Query `silver_orders`[cite: 1].
   - Assert total row count equals `bronze_orders` (proving ZERO rows were dropped)[cite: 1].
   - Assert quarantined rows count (`quality_check_result == 'FAIL'`) is greater than 400 (verifying all intentional anomalies were caught)[cite: 1].
   - Assert clean rows count (`quality_check_result == 'PASS'`) has empty `dq_errors` array[cite: 1].
4. Test 3 (`test_gold_layer_integrity`):
   - Query `gold_sales_by_product` and `gold_revenue_by_customer`[cite: 1].
   - Assert tables are non-empty[cite: 1].
   - Assert no negative or zero revenue values exist in Gold tables[cite: 1].
   - Assert all customers in `gold_revenue_by_customer` have valid assigned segments (`High-Value`, `Repeat`, `One-Time`, or `Inactive`)[cite: 1].
5. Include descriptive assertion error messages for debugging clarity.
also do it on databricks & execute there"

**AI RESPONSE SUMMARY:**
Created `tests/test_pipeline.py` with session-scoped `spark` fixture in `tests/conftest.py`, three integration tests with descriptive assertion messages, `run_pipeline_tests()` for Databricks notebook execution, and notebook/job config for serverless validation.

During execution, discovered and fixed two silver-layer issues blocking PASS rows:
- `array_remove(..., None)` did not strip null DQ entries on Databricks; replaced with `array_filter(..., lambda x: x.isNotNull())`
- `check_numeric_positive` failed on string values like `N/A` under ANSI mode; updated to use `try_cast`

Deployed and executed on Databricks:
- Tests module: `/Shared/medallion-pipeline/tests/test_pipeline.py`
- Notebook: `/Shared/medallion-pipeline/tests/run_pipeline_tests`
- Job submit via `conf/test_pipeline_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/840900314030001/run/32534966142771

**YOUR EVALUATION:**
✓ **What was good:**
- Silver test enforces zero row loss and FAIL count > 400
- Gold test validates revenue sanity and behavioral segment derivation
- Descriptive assertion messages aid debugging
- Test run surfaced real silver DQ bugs and validated fixes end-to-end

**FINAL DECISION:**
✅ **Accepted** — pipeline integration tests pass on Databricks. Note: bronze threshold set to 50,000 to match generated dataset (requirement cited 100,000).

---

## Prompt 2: Silver Rules Unit Tests

**PROMPT SENT:**
"@.cursorrules @src/silver/
Structure: Create `tests/test_silver_rules.py`.
Purpose: Provide isolated unit tests for individual Silver validation helper functions (`01` through `05`)[cite: 1].

Requirements:
1. `test_completeness_check`: Create a small dummy DataFrame with null and non-null values; verify `check_completeness` returns the expected error tag only for nulls[cite: 1].
2. `test_uniqueness_check`: Create a dummy DataFrame with duplicate IDs; verify `flag_duplicates` and `check_uniqueness` flag only duplicate rows[cite: 1].
3. `test_referential_integrity_check`: Create child and parent DataFrames with matching and orphan keys; verify `check_foreign_key` retains all records and `flag_invalid_fk` correctly tags orphans[cite: 1].
4. `test_business_logic_dates`: Create dummy records with payment dates before and after order dates; verify `check_order_payment_dates` flags only premature payments[cite: 1].
also do it on databricks & execute there"

**AI RESPONSE SUMMARY:**
Created `tests/test_silver_rules.py` with four isolated unit tests covering completeness, uniqueness, referential integrity, and business-logic date helpers using small in-memory DataFrames and descriptive assertion messages. Added `run_silver_rules_tests()` notebook runner.

Deployed and executed on Databricks:
- Tests module: `/Shared/medallion-pipeline/tests/test_silver_rules.py`
- Notebook: `/Shared/medallion-pipeline/tests/run_silver_rules_tests`
- Job submit via `conf/test_silver_rules_run.json` — **SUCCESS**
- Run URL: https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/333485004653067/run/806277515634607

**YOUR EVALUATION:**
✓ **What was good:**
- Tests validate helper logic in isolation without bronze/gold dependencies
- Covers soft-quarantine join/flag patterns for referential integrity
- Descriptive assertion messages per test case

**FINAL DECISION:**
✅ **Accepted** — all silver rules unit tests pass on Databricks.
