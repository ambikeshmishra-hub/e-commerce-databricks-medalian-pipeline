# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Create All Gold Tables
# MAGIC Executes all four gold SQL marts via `src.gold.create_gold_tables`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.gold.create_gold_tables import run_gold_pipeline

# COMMAND ----------

run_gold_pipeline(spark)
