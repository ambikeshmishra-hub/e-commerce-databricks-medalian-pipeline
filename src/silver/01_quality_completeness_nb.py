# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Completeness Quality Check
# MAGIC Validates `check_completeness()` against bronze customers data.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from pyspark.sql import functions as F

from src.silver import check_completeness

# COMMAND ----------

customers_df = spark.table("workspace.bronze.bronze_customers")

completeness_df = customers_df.select(
    "customer_id",
    "email",
    check_completeness("email", "NULL_EMAIL").alias("email_completeness_error"),
    check_completeness("customer_name", "NULL_CUSTOMER_NAME").alias(
        "name_completeness_error"
    ),
)

null_email_count = completeness_df.filter(
    F.col("email_completeness_error").isNotNull()
).count()

print(f"check_completeness validation complete.")
print(f"NULL_EMAIL flagged rows: {null_email_count:,}")
completeness_df.filter(F.col("email_completeness_error").isNotNull()).show(5, truncate=False)
