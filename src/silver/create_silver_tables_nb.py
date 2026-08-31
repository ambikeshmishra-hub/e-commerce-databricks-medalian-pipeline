# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Create Silver Tables
# MAGIC Applies modular DQ checks (01–05) to bronze orders and writes `workspace.silver.silver_orders`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.silver.create_silver_tables import run_silver_pipeline

# COMMAND ----------

silver_orders_df = run_silver_pipeline(spark)
print(f"silver_orders row count: {silver_orders_df.count():,}")
