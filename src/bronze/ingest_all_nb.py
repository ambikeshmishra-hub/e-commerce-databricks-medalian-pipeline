# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Ingest All
# MAGIC Orchestrates customers, orders, and products bronze ingestions via `src.bronze`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.bronze.ingest_all import run_bronze_ingestion

# COMMAND ----------

results = run_bronze_ingestion(spark)
print(f"Bronze ingest_all finished with {len(results)} datasets.")
