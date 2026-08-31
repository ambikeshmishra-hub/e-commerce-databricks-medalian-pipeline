# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Type Validation Quality Check
# MAGIC Validates `check_numeric_positive()` against bronze customers data.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from pyspark.sql import functions as F

from src.silver import check_numeric_positive

# COMMAND ----------

customers_df = spark.table("workspace.bronze.bronze_customers")

type_validation_df = customers_df.select(
    "customer_id",
    "lifetime_value",
    check_numeric_positive("lifetime_value", "NON_POSITIVE_LIFETIME_VALUE").alias(
        "lifetime_value_type_error"
    ),
)

flagged_count = type_validation_df.filter(
    F.col("lifetime_value_type_error").isNotNull()
).count()

print("check_numeric_positive validation complete.")
print(f"NON_POSITIVE_LIFETIME_VALUE flagged rows: {flagged_count:,}")
type_validation_df.filter(F.col("lifetime_value_type_error").isNotNull()).show(
    5, truncate=False
)
