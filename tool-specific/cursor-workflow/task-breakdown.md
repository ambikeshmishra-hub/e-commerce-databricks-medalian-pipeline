# Task Breakdown — Databricks Medallion Pipeline

Granular checklist-style task decomposition used across Cursor sessions to build the end-to-end pipeline. Tasks are ordered by dependency.

---

## Phase 0: Project Setup

- [x] Initialize repository structure (`src/`, `conf/`, `database/`, `ai-prompts/`, `data/`)
- [x] Create `.cursorrules` with Medallion architecture constraints
- [x] Create `tool-specific/cursor-workflow/spec.md` with CSV schemas and defect manifest
- [x] Create `requirements.txt` (pyspark, delta-spark, pandas, numpy, faker, pytest, databricks-cli)
- [x] Create `conf/databrickscfg.example` for CLI profile template
- [x] Create `database/schema.sql` for Unity Catalog schema bootstrap
- [x] Create `database/setup-notes.md` for CE environment setup
- [x] Configure Databricks CLI profile `community`

---

## Phase 1: Data Generation

- [x] Create `src/data_generation/generate_sample_data.py`
- [x] Implement `generate_customers()` with Faker (10,000 base rows)
- [x] Implement `generate_products()` with Faker (1,000 base rows)
- [x] Implement `generate_orders()` referencing valid customer/product IDs (50,000 rows)
- [x] Define `ISSUE_MANIFEST` with 700 intentional defects (460 spec + 240 supplemental)
- [x] Implement `inject_customer_issues()` — C01–C07 (120 defects)
- [x] Implement `inject_product_issues()` — P01–P06 (125 defects)
- [x] Implement `inject_order_issues()` — O01–O10 (455 defects)
- [x] Set `RANDOM_SEED = 42` for reproducibility
- [x] Implement `write_csv()` preserving blank NULL cells
- [x] Implement `summarize_issues()` manifest reporting
- [x] Run generator and verify output row counts
- [x] Document in `src/data_generation/DATA_GENERATION_NOTES.md`
- [x] Document in `database/seed-data-notes.md`
- [x] Log prompts to `ai-prompts/data-generation.md`

---

## Phase 2: Bronze Ingestion

### 2.1 Core Ingest Modules

- [x] Create `src/bronze/databricks_ingest.py` with CE-compatible functions
- [x] Create `src/bronze/01_ingest_customers.py`
- [x] Create `src/bronze/02_ingest_orders.py`
- [x] Create `src/bronze/03_ingest_products.py`
- [x] Create `src/bronze/ingest_all.py` orchestrator
- [x] Add `_ingested_at` via `current_timestamp()`
- [x] Add `_source_file` via `_metadata.file_path`
- [x] Write Delta tables: `workspace.bronze.bronze_{customers,orders,products}`
- [x] Use `overwrite` + `overwriteSchema` write mode

### 2.2 Notebook Wrappers

- [x] Create `src/bronze/01_ingest_customers_nb.py`
- [x] Create `src/bronze/02_ingest_orders_nb.py`
- [x] Create `src/bronze/03_ingest_products_nb.py`
- [x] Create `src/bronze/ingest_all_nb.py`
- [x] Add `sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")`

### 2.3 Package Init

- [x] Create `src/bronze/__init__.py` with dynamic module loading

### 2.4 Job Configs

- [x] Create `conf/bronze_ingest_customers_run.json`
- [x] Create `conf/bronze_ingest_orders_run.json`
- [x] Create `conf/bronze_ingest_products_run.json`
- [x] Create `conf/bronze_ingest_all_run.json`

### 2.5 Deployment & Validation

- [x] Upload CSVs to UC volume `workspace.default.medallion_data`
- [x] Import notebooks to `/Shared/medallion-pipeline/`
- [x] Execute bronze ingest job — verify row counts
- [x] Verify `_ingested_at` and `_source_file` populated
- [x] Log prompts to `ai-prompts/bronze-layer.md`

---

## Phase 3: Silver Quality Checks

### 3.1 DQ Modules

- [x] Create `src/silver/01_quality_completeness.py` — `check_completeness()`
- [x] Create `src/silver/02_quality_uniqueness.py` — `flag_duplicates()`, `check_uniqueness()`
- [x] Create `src/silver/03_quality_type_validation.py` — `check_numeric_positive()` with `try_cast`
- [x] Create `src/silver/04_quality_referential_integrity.py` — `check_foreign_key()` (LEFT JOIN), `flag_invalid_fk()`
- [x] Create `src/silver/05_quality_business_logic.py` — `check_order_payment_dates()`

### 3.2 Orchestrator

- [x] Create `src/silver/create_silver_tables.py`
- [x] Implement `_apply_orders_dq_checks()` composing all five modules
- [x] Build `dq_errors` via `array_filter(array(...), lambda x: x.isNotNull())`
- [x] Set `quality_check_result` = PASS/FAIL based on `size(dq_errors)`
- [x] Drop temp columns before write
- [x] Implement `DqMetricsSummary` and `print_dq_metrics_summary()`
- [x] Write `workspace.silver.silver_orders`

### 3.3 Notebook Wrappers

- [x] Create `src/silver/01_quality_completeness_nb.py`
- [x] Create `src/silver/02_quality_uniqueness_nb.py`
- [x] Create `src/silver/03_quality_type_validation_nb.py`
- [x] Create `src/silver/04_quality_referential_integrity_nb.py`
- [x] Create `src/silver/05_quality_business_logic_nb.py`
- [x] Create `src/silver/create_silver_tables_nb.py`

### 3.4 Package Init

- [x] Create `src/silver/__init__.py` with dynamic module loading

### 3.5 Job Configs

- [x] Create `conf/silver_01_quality_completeness_run.json`
- [x] Create `conf/silver_02_quality_uniqueness_run.json`
- [x] Create `conf/silver_03_quality_type_validation_run.json`
- [x] Create `conf/silver_04_quality_referential_integrity_run.json`
- [x] Create `conf/silver_05_quality_business_logic_run.json`
- [x] Create `conf/silver_create_silver_tables_run.json`

### 3.6 Deployment & Validation

- [x] Execute silver orchestrator job
- [x] Verify bronze/silver row-count parity
- [x] Verify FAIL count > 400
- [x] Verify PASS rows have empty `dq_errors`
- [x] Log prompts to `ai-prompts/silver-layer.md`

---

## Phase 4: Gold Aggregations

### 4.1 SQL Mart Files

- [x] Create `src/gold/01_sales_by_product.sql` — product revenue aggregation
- [x] Create `src/gold/02_revenue_by_customer.sql` — customer revenue aggregation
- [x] Create `src/gold/03_daily_weekly_trends.sql` — daily/weekly trends
- [x] Create `src/gold/04_customer_segmentation.sql` — behavioral segmentation
- [x] Ensure all SQL includes `WHERE quality_check_result = 'PASS'`

### 4.2 Orchestrator

- [x] Create `src/gold/create_gold_tables.py` — executes all four SQL files
- [x] Create `src/gold/create_gold_tables_nb.py`

### 4.3 Notebook Wrappers (Individual Marts)

- [x] Create `src/gold/01_sales_by_product_nb.py`
- [x] Create `src/gold/02_revenue_by_customer_nb.py`
- [x] Create `src/gold/03_daily_weekly_trends_nb.py`
- [x] Create `src/gold/04_customer_segmentation_nb.py`

### 4.4 Package Init

- [x] Create `src/gold/__init__.py`

### 4.5 Job Configs

- [x] Create `conf/gold_01_sales_by_product_run.json`
- [x] Create `conf/gold_02_revenue_by_customer_run.json`
- [x] Create `conf/gold_03_daily_weekly_trends_run.json`
- [x] Create `conf/gold_04_customer_segmentation_run.json`
- [x] Create `conf/gold_create_gold_tables_run.json`

### 4.6 Deployment & Validation

- [x] Execute gold orchestrator job
- [x] Verify all four gold tables non-empty
- [x] Verify revenue values positive and non-null
- [x] Log prompts to `ai-prompts/gold-layer.md`

---

## Phase 5: Dashboard Queries

- [x] Create `src/dashboard/dashboard_queries.sql` — three BI tile queries
  - [x] Tile 1: Top 10 Products by Revenue (horizontal bar chart)
  - [x] Tile 2: Customer Revenue Distribution (histogram)
  - [x] Tile 3: Customer Segmentation Breakdown (pie/donut chart)
- [x] Create `src/dashboard/run_dashboard_queries.py`
- [x] Create `src/dashboard/dashboard_queries_nb.py`
- [x] Create `src/dashboard/dashboard_guide_nb.py`
- [x] Create `src/dashboard/DASHBOARD_GUIDE.md`
- [x] Create `src/dashboard/__init__.py`
- [x] Create `conf/dashboard_queries_run.json`
- [x] Create `conf/dashboard_guide_run.json`
- [x] Execute dashboard query job
- [x] Log prompts to `ai-prompts/dashboard.md`

---

## Phase 6: Unit & Integration Testing

### 6.1 Test Infrastructure

- [x] Create `tests/conftest.py` — session-scoped Spark fixture
- [x] Create `tests/__init__.py`

### 6.2 Integration Tests

- [x] Create `tests/test_pipeline.py`
  - [x] `test_bronze_ingestion_counts` — row volumes + metadata columns
  - [x] `test_silver_soft_quarantine_anomaly_detection` — parity + FAIL > 400
  - [x] `test_gold_layer_integrity` — revenue sanity + segment validation

### 6.3 Unit Tests

- [x] Create `tests/test_silver_rules.py`
  - [x] Test `check_completeness`
  - [x] Test `flag_duplicates` / `check_uniqueness`
  - [x] Test `check_foreign_key` / `flag_invalid_fk`
  - [x] Test `check_order_payment_dates`

### 6.4 Databricks Test Notebooks

- [x] Create `tests/test_pipeline_nb.py` — refresh silver+gold, run integration tests
- [x] Create `tests/test_silver_rules_nb.py` — run unit tests
- [x] Create `conf/test_pipeline_run.json`
- [x] Create `conf/test_silver_rules_run.json`

### 6.5 Validation

- [x] Execute test jobs on Databricks serverless
- [x] All tests PASS
- [x] Log prompts to `ai-prompts/debugging.md`

---

## Phase 7: Documentation

- [x] Create `candidate-info.md` — metadata, environment, quickstart
- [x] Create `database/reflection.md` — technical reflection on Cursor usage
- [x] Create `database/debugging-notes.md` — documented issues and fixes
- [x] Create `database/final-ai-usage-summary.md` — AI metrics and governance
- [x] Create `requirements-analysis.md`
- [x] Create `design-notes.md`
- [x] Create `data-model.md`
- [x] Create `data-quality-strategy.md`
- [x] Create `tool-workflow.md`
- [x] Create `database/seed-data-notes.md`
- [x] Create `tool-specific/cursor-workflow/project-context.md`
- [x] Create `tool-specific/cursor-workflow/cursor-rules-or-instructions.md`
- [x] Create `tool-specific/cursor-workflow/task-breakdown.md` (this file)
- [x] Create `src/data_generation/DATA_GENERATION_NOTES.md`
- [x] Create `src/__init__.py`
- [x] Log prompts to `ai-prompts/documentation.md`

---

## Phase 8: Future Work (Not Started)

- [ ] Create `silver_customers` and `silver_products` tables
- [ ] Migrate to Delta Live Tables (DLT) orchestration
- [ ] Integrate Great Expectations checkpoint suites
- [ ] Add CI/CD via Databricks Repos + GitHub Actions
- [ ] Implement incremental bronze ingest (append + merge)
- [ ] Add table partitioning by `order_date`
- [ ] Populate `README.md` with full project overview
- [ ] Extend silver DQ to cover customer/product injected defects (C03–C07, P01–P06)
- [ ] Add amount reconciliation rule for O06 (`total_amount` mismatch)
- [ ] Add enum validation for O08 (`order_status`)

---

## Execution Order Summary

```
Phase 0 (Setup)
    │
    ▼
Phase 1 (Data Gen) ──▶ Upload CSVs to UC volume
    │
    ▼
Phase 2 (Bronze) ──▶ bronze_{customers,orders,products}
    │
    ▼
Phase 3 (Silver) ──▶ silver_orders (DQ + quarantine)
    │
    ▼
Phase 4 (Gold) ──▶ gold_* (PASS-only marts)
    │
    ▼
Phase 5 (Dashboard) ──▶ BI tile queries
    │
    ▼
Phase 6 (Tests) ──▶ Validate end-to-end integrity
    │
    ▼
Phase 7 (Docs) ──▶ Assessment deliverables
```

---

## Databricks Job Execution Sequence

```bash
# 1. Bronze
databricks jobs submit --json @conf/bronze_ingest_all_run.json --profile community

# 2. Silver
databricks jobs submit --json @conf/silver_create_silver_tables_run.json --profile community

# 3. Gold
databricks jobs submit --json @conf/gold_create_gold_tables_run.json --profile community

# 4. Dashboard
databricks jobs submit --json @conf/dashboard_queries_run.json --profile community

# 5. Tests
databricks jobs submit --json @conf/test_pipeline_run.json --profile community
databricks jobs submit --json @conf/test_silver_rules_run.json --profile community
```
