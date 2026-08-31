# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Business Logic Quality Check
# MAGIC Validates `check_order_payment_dates()` against bronze orders data.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from pyspark.sql import functions as F

from src.silver import check_order_payment_dates

# COMMAND ----------

orders_df = spark.table("workspace.bronze.bronze_orders")

business_logic_df = orders_df.select(
    "order_id",
    "order_date",
    "payment_date",
    check_order_payment_dates(
        "order_date", "payment_date", "PAYMENT_BEFORE_ORDER_DATE"
    ).alias("payment_date_logic_error"),
)

invalid_payment_count = business_logic_df.filter(
    F.col("payment_date_logic_error").isNotNull()
).count()

print("check_order_payment_dates validation complete.")
print(f"PAYMENT_BEFORE_ORDER_DATE flagged rows: {invalid_payment_count:,}")
business_logic_df.filter(F.col("payment_date_logic_error").isNotNull()).show(
    5, truncate=False
)
