# Candidate Information — E-Commerce Medallion Pipeline

Complete candidate, environment, and execution metadata for the technical assessment submission.

---

## 1. Candidate Metadata

| Field | Value |
|---|---|
| **Name** | Ambikesh Mishra |
| **Role** | Senior Data Engineer
| **Primary Stack** | Python / PySpark, Delta Lake, SQL, Databricks |
| **Primary AI Tool** | Cursor (Claude 3.5 Sonnet engine) |
| **Project Option** | Data Pipeline (Medallion Architecture) |
| **Assessment Start Date** | 2026-08-31 |
| **Submission Date** | 2026-08-31 |

**Repository:** `databricks-medallion-pipeline`  
**Workspace:** Databricks Community Edition (`workspace` catalog)  
**Architecture:** Bronze (raw ingest) → Silver (soft-quarantine DQ) → Gold (PASS-only analytics)

---

## 2. Tools & Runtime Environment

### Cloud Platform

| Component | Configuration |
|---|---|
| **Platform** | Databricks Community Edition |
| **Cluster Type** | Serverless compute (single-node job execution) |
| **Workspace URL** | `https://dbc-8af8048c-3b55.cloud.databricks.com` |
| **CLI Profile** | `community` (see `conf/databrickscfg.example`) |
| **Catalog / Schemas** | `workspace.bronze`, `workspace.silver`, `workspace.gold` |
| **Source Data Volume** | `dbfs:/Volumes/workspace/default/medallion_data/` |

### Databricks Runtime

| Component | Version |
|---|---|
| **Databricks Runtime** | 13.3+ LTS (serverless `environment_version: 3`) |
| **Apache Spark** | 3.4.1 |
| **Scala** | 2.12 |
| **Delta Lake** | Enabled via `DeltaSparkSessionExtension` |

### Python Libraries

Installed via `requirements.txt`:

| Library | Purpose |
|---|---|
| `pyspark` | Spark DataFrame API |
| `delta-spark` | Delta Lake table reads/writes |
| `pandas` / `numpy` | Local data generation |
| `faker` | Synthetic customer/product data |
| `pytest` | Automated pipeline & unit tests |
| `databricks-cli` | Workspace deploy and job execution |

---

## 3. Quickstart Pipeline Run Sequence

Run all commands from the repository root after cloning.

### Step 0 — Local Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure Databricks credentials in `~/.databrickscfg` using `conf/databrickscfg.example` as a template (`[community]` profile).

### Step 1 — Generate Synthetic CSV Data

```bash
python src/data_generation/generate_sample_data.py
```

**Outputs:** `data/customers.csv`, `data/orders.csv`, `data/products.csv` (~700 intentional DQ defects)

### Step 2 — Upload CSVs to Databricks (Unity Catalog Volume)

```bash
databricks fs cp --overwrite data/customers.csv \
  dbfs:/Volumes/workspace/default/medallion_data/customers.csv --profile community

databricks fs cp --overwrite data/orders.csv \
  dbfs:/Volumes/workspace/default/medallion_data/orders.csv --profile community

databricks fs cp --overwrite data/products.csv \
  dbfs:/Volumes/workspace/default/medallion_data/products.csv --profile community
```

### Step 3 — Deploy Project Code to Workspace (first run only)

```bash
# Example: import bronze orchestrator notebook
databricks workspace import \
  "/Shared/medallion-pipeline/bronze/ingest_all" \
  --file src/bronze/ingest_all_nb.py \
  --format SOURCE --language PYTHON --overwrite --profile community
```

Repeat workspace imports for `src/`, `silver/`, `gold/`, `dashboard/`, and `tests/` modules as documented in each layer's notebooks. All job configs under `conf/` reference `/Shared/medallion-pipeline/` paths.

### Step 4 — Full Medallion Pipeline (Bronze → Silver → Gold → Dashboard)

Run all four layers as a single multi-task workflow:

```bash
# Deploy latest code (first run or after code changes)
bash scripts/deploy_workspace.sh

# Execute end-to-end pipeline (one-shot submit)
databricks jobs submit --json @conf/medallion_pipeline_run.json \
  --profile community --timeout 60m
```

**Persistent job** (re-runnable from Workflows UI):

| Asset | Value |
|---|---|
| Job name | `medallion-pipeline-bronze-silver-gold-dashboard` |
| Job ID | `460413873521986` |
| Job URL | https://dbc-8af8048c-3b55.cloud.databricks.com/?o=7474657867930807#job/460413873521986 |

```bash
# Trigger the persistent job
databricks jobs run-now 460413873521986 --profile community
```

**Published Lakeview dashboard:**

| Asset | Value |
|---|---|
| Name | E-Commerce Gold Analytics |
| Dashboard ID | `01f1a56b998419c7874820200ea1396a` |
| URL | https://dbc-8af8048c-3b55.cloud.databricks.com/sql/dashboardsv3/01f1a56b998419c7874820200ea1396a |

Dashboard-only republish (after gold refresh):

```bash
databricks jobs submit --json @conf/publish_dashboard_run.json \
  --profile community --timeout 30m
```

### Step 5 — Bronze Layer Ingestion (individual layer)

```bash
databricks jobs submit --json @conf/bronze_ingest_all_run.json \
  --profile community --timeout 30m
```

**Creates:** `workspace.bronze.bronze_customers`, `workspace.bronze.bronze_orders`, `workspace.bronze.bronze_products`

### Step 6 — Silver Layer (Soft-Quarantine DQ)

```bash
databricks jobs submit --json @conf/silver_create_silver_tables_run.json \
  --profile community --timeout 30m
```

**Creates:** `workspace.silver.silver_orders` with `dq_errors` and `quality_check_result` columns

### Step 7 — Gold Layer (PASS-Only Analytics Marts)

```bash
databricks jobs submit --json @conf/gold_create_gold_tables_run.json \
  --profile community --timeout 30m
```

**Creates:**

- `workspace.gold.gold_sales_by_product`
- `workspace.gold.gold_revenue_by_customer`
- `workspace.gold.gold_daily_weekly_trends`
- `workspace.gold.gold_customer_segmentation`

### Step 8 — Pytest Validation

**Local (requires materialized Delta tables or active Spark session):**

```bash
pytest tests/test_pipeline.py tests/test_silver_rules.py -v
```

**Databricks (recommended — validates live workspace tables):**

```bash
# End-to-end pipeline integration tests (bronze → silver → gold)
databricks jobs submit --json @conf/test_pipeline_run.json \
  --profile community --timeout 45m

# Isolated silver DQ helper unit tests
databricks jobs submit --json @conf/test_silver_rules_run.json \
  --profile community --timeout 30m
```

### Optional — Dashboard Queries

```bash
databricks jobs submit --json @conf/dashboard_queries_run.json \
  --profile community --timeout 30m
```

See `src/dashboard/DASHBOARD_GUIDE.md` for Databricks SQL Dashboard UI setup.

---

## 4. Key Workspace Paths

| Asset | Path |
|---|---|
| Project root (workspace) | `/Shared/medallion-pipeline/` |
| Bronze notebooks | `/Shared/medallion-pipeline/bronze/` |
| Silver notebooks | `/Shared/medallion-pipeline/silver/` |
| Gold notebooks | `/Shared/medallion-pipeline/gold/` |
| Test notebooks | `/Shared/medallion-pipeline/tests/` |
| Job configs (local) | `conf/*.json` |

---

## 5. Validation Summary

| Layer | Tables | DQ / Filter Rule |
|---|---|---|
| Bronze | `bronze_customers`, `bronze_orders`, `bronze_products` | Lossless ingest + `_ingested_at`, `_source_file` |
| Silver | `silver_orders` | Soft-quarantine: `quality_check_result` PASS/FAIL, `dq_errors` array |
| Gold | 4 analytical marts | **Strict filter:** `quality_check_result = 'PASS'` only |

**Test suites:**

- `tests/test_pipeline.py` — integration tests (row counts, quarantine, gold integrity)
- `tests/test_silver_rules.py` — unit tests for DQ helpers (modules 01–05)
