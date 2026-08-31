# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Ingest Customers
# MAGIC Reads `customers.csv` from the medallion data volume and writes `workspace.bronze.bronze_customers`.

# COMMAND ----------

"""Bronze-layer ingestion for the customers CSV source on Databricks."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

BRONZE_TABLE_NAME = "workspace.bronze.bronze_customers"
DEFAULT_SOURCE_PATH = "dbfs:/Volumes/workspace/default/medallion_data/customers.csv"


def ingest_customers(
    spark: SparkSession,
    source_path: str = DEFAULT_SOURCE_PATH,
) -> DataFrame:
    """Read customers CSV, append audit metadata, and write the bronze Delta table."""
    customers_df: DataFrame = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(source_path)
    )

    bronze_df: DataFrame = customers_df.withColumn(
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
bronze_customers_df = ingest_customers(spark)
print(f"Wrote Delta table: {BRONZE_TABLE_NAME}")
print(f"Row count: {bronze_customers_df.count():,}")
