# Environment Setup Notes

Detailed guide for configuring the Databricks workspace, importing repository files, bootstrapping schemas, and setting data paths for the Medallion pipeline.

---

## 1. Prerequisites

| Requirement | Details |
|---|---|
| **Local OS** | macOS / Linux (commands below use bash) |
| **Python** | 3.10+ |
| **Databricks** | Community Edition workspace |
| **CLI** | `databricks-cli` (see `requirements.txt`) |
| **Repo** | Clone `databricks-medallion-pipeline` locally |

---

## 2. Local Python Environment

```bash
cd databricks-medallion-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Generate synthetic CSVs locally:

```bash
python src/data_generation/generate_sample_data.py
```

Outputs land in `data/customers.csv`, `data/orders.csv`, `data/products.csv`.

---

## 3. Databricks CLI Configuration

1. Copy `conf/databrickscfg.example` → `~/.databrickscfg`
2. Generate a Personal Access Token: **Settings → Developer → Access tokens**
3. Configure the `[community]` profile:

```ini
[community]
host = https://dbc-8af8048c-3b55.cloud.databricks.com
token = dapiYOUR_TOKEN_HERE
```

4. Verify connectivity:

```bash
databricks workspace list /Shared --profile community
```

> **Never commit tokens.** Keep credentials only in `~/.databrickscfg`.

---

## 4. Workspace & Compute Configuration

### Community Edition Constraints

| Setting | Value |
|---|---|
| **Catalog** | `workspace` (Unity Catalog) |
| **Compute** | Serverless (`environment_version: 3` in job JSONs) |
| **Schemas** | `workspace.bronze`, `workspace.silver`, `workspace.gold` |
| **Source data** | UC Volume — **not** public DBFS root |

Community Edition blocks writes to `dbfs:/FileStore/...`. Use the UC volume path instead (see Section 6).

### Job Configuration Pattern

All pipeline jobs under `conf/` use serverless environments:

```json
{
  "environment_key": "serverless",
  "spec": { "environment_version": "3" }
}
```

Submit with:

```bash
databricks jobs submit --json @conf/<job>.json --profile community --timeout 30m
```

---

## 5. Bootstrap Schemas via `database/schema.sql`

1. Open **Databricks SQL → SQL Editor**
2. Set default catalog to `workspace`
3. Paste and run `database/schema.sql`

This creates:

- `workspace.bronze`
- `workspace.silver`
- `workspace.gold`

**Note:** Delta **tables** are not defined in `schema.sql`. They are created by pipeline jobs using `CREATE OR REPLACE TABLE ... AS` (gold) or `.saveAsTable()` (bronze/silver). The schema file bootstraps namespaces only.

Alternatively, schemas are auto-created by orchestrators:

```python
spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.bronze")
```

---

## 6. Data Path Configuration

### Unity Catalog Volume (Recommended for CE)

Create the volume once (SQL Editor or CLI):

```sql
CREATE VOLUME IF NOT EXISTS workspace.default.medallion_data;
```

Upload CSVs:

```bash
databricks fs cp --overwrite data/customers.csv \
  dbfs:/Volumes/workspace/default/medallion_data/customers.csv --profile community

databricks fs cp --overwrite data/orders.csv \
  dbfs:/Volumes/workspace/default/medallion_data/orders.csv --profile community

databricks fs cp --overwrite data/products.csv \
  dbfs:/Volumes/workspace/default/medallion_data/products.csv --profile community
```

### Path Reference Table

| Purpose | Path |
|---|---|
| **Local CSVs** | `data/*.csv` |
| **Databricks source CSVs** | `dbfs:/Volumes/workspace/default/medallion_data/*.csv` |
| **Bronze ingest code default** | `DATA_VOLUME_BASE` in `src/bronze/databricks_ingest.py` |
| **Workspace project root** | `/Shared/medallion-pipeline/` |
| **Job configs** | `conf/*.json` |

Update `conf/community_config.json` if workspace URL or profile name differs.

---

## 7. Import Repository Files to Workspace

Import Python modules, SQL, and notebooks to `/Shared/medallion-pipeline/`:

```bash
# Example: bronze orchestrator notebook
databricks workspace mkdirs "/Shared/medallion-pipeline/bronze" --profile community

databricks workspace import \
  "/Shared/medallion-pipeline/bronze/ingest_all" \
  --file src/bronze/ingest_all_nb.py \
  --format SOURCE --language PYTHON --overwrite --profile community

# Example: raw Python module
databricks workspace import \
  "/Shared/medallion-pipeline/src/silver/create_silver_tables.py" \
  --file src/silver/create_silver_tables.py \
  --format RAW --overwrite --profile community
```

Repeat for `src/`, `silver/`, `gold/`, `dashboard/`, and `tests/` directories. Each `*_nb.py` notebook must be imported with `--format SOURCE --language PYTHON`; `.py` modules and `.sql` files use `--format RAW`.

Notebooks insert the project into `sys.path`:

```python
sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")
```

---

## 8. Pipeline Execution Order

Run jobs in sequence after setup:

```bash
# 1. Bronze
databricks jobs submit --json @conf/bronze_ingest_all_run.json --profile community --timeout 30m

# 2. Silver
databricks jobs submit --json @conf/silver_create_silver_tables_run.json --profile community --timeout 30m

# 3. Gold
databricks jobs submit --json @conf/gold_create_gold_tables_run.json --profile community --timeout 30m

# 4. Tests (optional validation)
databricks jobs submit --json @conf/test_pipeline_run.json --profile community --timeout 45m
databricks jobs submit --json @conf/test_silver_rules_run.json --profile community --timeout 30m
```

See `candidate-info.md` for the full quickstart reference.

---

## 9. Verify Setup

| Check | Command / Query |
|---|---|
| CSVs in volume | `databricks fs ls dbfs:/Volumes/workspace/default/medallion_data/ --profile community` |
| Bronze tables | `SELECT COUNT(*) FROM workspace.bronze.bronze_orders` |
| Silver DQ | `SELECT quality_check_result, COUNT(*) FROM workspace.silver.silver_orders GROUP BY 1` |
| Gold marts | `SELECT COUNT(*) FROM workspace.gold.gold_sales_by_product` |

---

## 10. Common Setup Pitfalls

| Symptom | Resolution |
|---|---|
| `401 Unauthorized` | Regenerate `dapi…` token; update `~/.databrickscfg` |
| `403 Public DBFS root disabled` | Switch to UC volume path (Section 6) |
| `ModuleNotFoundError: src` | Verify `sys.path.insert` and workspace imports under `/Shared/medallion-pipeline/` |
| `input_file_name()` error on UC | Use `_metadata.file_path` in Databricks notebook variants (`*_nb.py`) |
