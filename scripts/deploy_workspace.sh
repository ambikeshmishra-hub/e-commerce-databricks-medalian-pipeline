#!/usr/bin/env bash
# Deploy medallion pipeline source code and notebooks to Databricks workspace.
set -euo pipefail

PROFILE="${DATABRICKS_PROFILE:-community}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS="/Shared/medallion-pipeline"

echo "Deploying to ${WS} (profile: ${PROFILE})"

databricks workspace mkdirs "${WS}/bronze" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/silver" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/gold" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/dashboard" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/tests" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/src/bronze" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/src/silver" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/src/gold" --profile "${PROFILE}" || true
databricks workspace mkdirs "${WS}/src/dashboard" --profile "${PROFILE}" || true

import_notebook() {
  local dest="$1"
  local src="$2"
  databricks workspace import "${dest}" --file "${src}" \
    --format SOURCE --language PYTHON --overwrite --profile "${PROFILE}"
}

import_raw() {
  local dest="$1"
  local src="$2"
  databricks workspace import "${dest}" --file "${src}" \
    --format RAW --overwrite --profile "${PROFILE}"
}

# Bronze
import_notebook "${WS}/bronze/ingest_all" "${ROOT}/src/bronze/ingest_all_nb.py"
import_notebook "${WS}/bronze/ingest_customers" "${ROOT}/src/bronze/01_ingest_customers_nb.py"
import_notebook "${WS}/bronze/ingest_orders" "${ROOT}/src/bronze/02_ingest_orders_nb.py"
import_notebook "${WS}/bronze/ingest_products" "${ROOT}/src/bronze/03_ingest_products_nb.py"
import_raw "${WS}/src/bronze/databricks_ingest.py" "${ROOT}/src/bronze/databricks_ingest.py"
import_raw "${WS}/src/bronze/01_ingest_customers.py" "${ROOT}/src/bronze/01_ingest_customers.py"
import_raw "${WS}/src/bronze/02_ingest_orders.py" "${ROOT}/src/bronze/02_ingest_orders.py"
import_raw "${WS}/src/bronze/03_ingest_products.py" "${ROOT}/src/bronze/03_ingest_products.py"
import_raw "${WS}/src/bronze/ingest_all.py" "${ROOT}/src/bronze/ingest_all.py"
import_raw "${WS}/src/bronze/__init__.py" "${ROOT}/src/bronze/__init__.py"

# Silver
import_notebook "${WS}/silver/create_silver_tables" "${ROOT}/src/silver/create_silver_tables_nb.py"
for f in "${ROOT}"/src/silver/0*_quality_*.py; do
  base="$(basename "${f}")"
  import_raw "${WS}/src/silver/${base}" "${f}"
done
import_raw "${WS}/src/silver/create_silver_tables.py" "${ROOT}/src/silver/create_silver_tables.py"
import_raw "${WS}/src/silver/__init__.py" "${ROOT}/src/silver/__init__.py"

# Gold
import_notebook "${WS}/gold/create_gold_tables" "${ROOT}/src/gold/create_gold_tables_nb.py"
for f in "${ROOT}"/src/gold/*.sql; do
  base="$(basename "${f}")"
  import_raw "${WS}/src/gold/${base}" "${f}"
done
import_raw "${WS}/src/gold/create_gold_tables.py" "${ROOT}/src/gold/create_gold_tables.py"
import_raw "${WS}/src/gold/__init__.py" "${ROOT}/src/gold/__init__.py"

# Dashboard
import_notebook "${WS}/dashboard/dashboard_queries" "${ROOT}/src/dashboard/dashboard_queries_nb.py"
import_notebook "${WS}/dashboard/dashboard_guide" "${ROOT}/src/dashboard/dashboard_guide_nb.py"
import_notebook "${WS}/dashboard/publish_dashboard" "${ROOT}/src/dashboard/publish_dashboard_nb.py"
import_raw "${WS}/src/dashboard/dashboard_queries.sql" "${ROOT}/src/dashboard/dashboard_queries.sql"
import_raw "${WS}/src/dashboard/run_dashboard_queries.py" "${ROOT}/src/dashboard/run_dashboard_queries.py"
import_raw "${WS}/src/dashboard/publish_dashboard.py" "${ROOT}/src/dashboard/publish_dashboard.py"
import_raw "${WS}/src/dashboard/DASHBOARD_GUIDE.md" "${ROOT}/src/dashboard/DASHBOARD_GUIDE.md"
import_raw "${WS}/src/dashboard/__init__.py" "${ROOT}/src/dashboard/__init__.py"
import_raw "${WS}/src/__init__.py" "${ROOT}/src/__init__.py"

echo "Deploy complete."
