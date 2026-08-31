# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard — BI Tile Queries
# MAGIC Executes production-ready dashboard queries from `dashboard_queries.sql`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.dashboard.run_dashboard_queries import run_dashboard_queries

# COMMAND ----------

run_dashboard_queries(spark)
