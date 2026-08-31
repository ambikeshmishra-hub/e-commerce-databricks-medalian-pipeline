# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Customer Segmentation
# MAGIC Creates `workspace.gold.gold_customer_segmentation` from PASS silver orders.

# COMMAND ----------

SQL_FILE_PATH = "/Workspace/Shared/medallion-pipeline/src/gold/04_customer_segmentation.sql"

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.gold")

with open(SQL_FILE_PATH, encoding="utf-8") as sql_file:
    customer_segmentation_sql = sql_file.read()

spark.sql(customer_segmentation_sql)

# COMMAND ----------

gold_customer_segmentation_df = spark.table("workspace.gold.gold_customer_segmentation")

print(f"gold_customer_segmentation row count: {gold_customer_segmentation_df.count():,}")
gold_customer_segmentation_df.orderBy("total_revenue", ascending=False).show(truncate=False)
