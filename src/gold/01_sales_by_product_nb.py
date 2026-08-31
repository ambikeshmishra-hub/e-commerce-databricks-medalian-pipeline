# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Sales by Product
# MAGIC Creates `workspace.gold.gold_sales_by_product` from PASS silver orders joined to bronze products.

# COMMAND ----------

SQL_FILE_PATH = "/Workspace/Shared/medallion-pipeline/src/gold/01_sales_by_product.sql"

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.gold")

with open(SQL_FILE_PATH, encoding="utf-8") as sql_file:
    sales_by_product_sql = sql_file.read()

spark.sql(sales_by_product_sql)

# COMMAND ----------

gold_sales_by_product_df = spark.table("workspace.gold.gold_sales_by_product")

print(f"gold_sales_by_product row count: {gold_sales_by_product_df.count():,}")
gold_sales_by_product_df.orderBy("total_revenue", ascending=False).show(10, truncate=False)
