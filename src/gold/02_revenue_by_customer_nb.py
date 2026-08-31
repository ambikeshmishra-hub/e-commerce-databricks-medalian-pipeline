# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Revenue by Customer
# MAGIC Creates `workspace.gold.gold_revenue_by_customer` from PASS silver orders joined to bronze customers.

# COMMAND ----------

SQL_FILE_PATH = "/Workspace/Shared/medallion-pipeline/src/gold/02_revenue_by_customer.sql"

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.gold")

with open(SQL_FILE_PATH, encoding="utf-8") as sql_file:
    revenue_by_customer_sql = sql_file.read()

spark.sql(revenue_by_customer_sql)

# COMMAND ----------

gold_revenue_by_customer_df = spark.table("workspace.gold.gold_revenue_by_customer")

print(f"gold_revenue_by_customer row count: {gold_revenue_by_customer_df.count():,}")
gold_revenue_by_customer_df.orderBy("total_revenue", ascending=False).show(10, truncate=False)
