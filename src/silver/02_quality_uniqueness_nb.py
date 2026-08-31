# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Uniqueness Quality Check
# MAGIC Validates `flag_duplicates()` and `check_uniqueness()` against bronze customers data.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from pyspark.sql import functions as F

from src.silver import check_uniqueness, flag_duplicates

# COMMAND ----------

customers_df = spark.table("workspace.bronze.bronze_customers")

uniqueness_df = flag_duplicates(customers_df, id_col="customer_id").select(
    "customer_id",
    "email",
    "row_occurrence_count",
    check_uniqueness("row_occurrence_count", "DUPLICATE_CUSTOMER_ID").alias(
        "customer_id_uniqueness_error"
    ),
)

duplicate_count = uniqueness_df.filter(
    F.col("customer_id_uniqueness_error").isNotNull()
).count()

print("check_uniqueness validation complete.")
print(f"DUPLICATE_CUSTOMER_ID flagged rows: {duplicate_count:,}")
uniqueness_df.filter(F.col("customer_id_uniqueness_error").isNotNull()).show(
    5, truncate=False
)
