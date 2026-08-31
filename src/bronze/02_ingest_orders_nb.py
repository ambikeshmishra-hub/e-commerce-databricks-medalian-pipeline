# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Ingest Orders
# MAGIC Reads `orders.csv` from the medallion data volume and writes `workspace.bronze.bronze_orders`.

# COMMAND ----------

"""Bronze-layer ingestion for the orders CSV source on Databricks."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

BRONZE_TABLE_NAME = "workspace.bronze.bronze_orders"
DEFAULT_SOURCE_PATH = "dbfs:/Volumes/workspace/default/medallion_data/orders.csv"


def ingest_orders(
    spark: SparkSession,
    source_path: str = DEFAULT_SOURCE_PATH,
) -> DataFrame:
    """Read orders CSV, append audit metadata, and write the bronze Delta table."""
    orders_df: DataFrame = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(source_path)
    )

    bronze_df: DataFrame = orders_df.withColumn(
        "_ingested_at", F.current_timestamp()
    ).withColumn("_source_file", F.col("_metadata.file_path"))

    (
        bronze_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(BRONZE_TABLE_NAME)
    )

    return bronze_df

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.bronze")
bronze_orders_df = ingest_orders(spark)
print(f"Wrote Delta table: {BRONZE_TABLE_NAME}")
print(f"Row count: {bronze_orders_df.count():,}")
