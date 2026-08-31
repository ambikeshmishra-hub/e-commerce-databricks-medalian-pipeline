# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Daily & Weekly Trends
# MAGIC Creates `workspace.gold.gold_daily_weekly_trends` from PASS silver orders.

# COMMAND ----------

SQL_FILE_PATH = "/Workspace/Shared/medallion-pipeline/src/gold/03_daily_weekly_trends.sql"

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.gold")

with open(SQL_FILE_PATH, encoding="utf-8") as sql_file:
    daily_weekly_trends_sql = sql_file.read()

spark.sql(daily_weekly_trends_sql)

# COMMAND ----------

gold_daily_weekly_trends_df = spark.table("workspace.gold.gold_daily_weekly_trends")

print(f"gold_daily_weekly_trends row count: {gold_daily_weekly_trends_df.count():,}")
gold_daily_weekly_trends_df.orderBy("order_date").show(10, truncate=False)
