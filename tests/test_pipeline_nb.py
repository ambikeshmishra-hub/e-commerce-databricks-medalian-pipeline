# Databricks notebook source
# MAGIC %md
# MAGIC # Pipeline Integration Tests
# MAGIC Materializes silver/gold tables if needed, then runs `tests/test_pipeline.py`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.gold.create_gold_tables import run_gold_pipeline
from src.silver.create_silver_tables import run_silver_pipeline
from tests.test_pipeline import run_pipeline_tests

BRONZE_ORDERS = "workspace.bronze.bronze_orders"
SILVER_ORDERS = "workspace.silver.silver_orders"
GOLD_SALES = "workspace.gold.gold_sales_by_product"

# COMMAND ----------

bronze_count = spark.table(BRONZE_ORDERS).count()
silver_count = spark.table(SILVER_ORDERS).count()
gold_sales_count = spark.table(GOLD_SALES).count()

print(f"[tests] bronze_orders rows: {bronze_count:,}")
print(f"[tests] silver_orders rows: {silver_count:,}")
print(f"[tests] gold_sales_by_product rows: {gold_sales_count:,}")

print("[tests] Refreshing silver and gold tables before validation.")
run_silver_pipeline(spark)
run_gold_pipeline(spark)

# COMMAND ----------

run_pipeline_tests(spark)
