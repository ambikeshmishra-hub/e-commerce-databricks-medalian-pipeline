# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Referential Integrity Quality Check
# MAGIC Validates `check_foreign_key()` and `flag_invalid_fk()` against bronze orders/customers data.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from pyspark.sql import functions as F

from src.silver import check_foreign_key, flag_invalid_fk

# COMMAND ----------

orders_df = spark.table("workspace.bronze.bronze_orders")
customers_df = spark.table("workspace.bronze.bronze_customers")

orders_with_customers = check_foreign_key(
    orders_df,
    customers_df,
    fk_col="customer_id",
    parent_pk_col="customer_id",
    alias_col="matched_customer_id",
)

referential_integrity_df = orders_with_customers.select(
    "order_id",
    "customer_id",
    "matched_customer_id",
    flag_invalid_fk(
        "matched_customer_id", "customer_id", "INVALID_CUSTOMER_ID_FK"
    ).alias("customer_id_fk_error"),
)

invalid_fk_count = referential_integrity_df.filter(
    F.col("customer_id_fk_error").isNotNull()
).count()

print("flag_invalid_fk validation complete.")
print(f"INVALID_CUSTOMER_ID_FK flagged rows: {invalid_fk_count:,}")
referential_integrity_df.filter(F.col("customer_id_fk_error").isNotNull()).show(
    5, truncate=False
)
