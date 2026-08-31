"""Databricks-compatible bronze ingestion functions for Unity Catalog."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

DATA_VOLUME_BASE = "dbfs:/Volumes/workspace/default/medallion_data"


def ingest_customers(
    spark: SparkSession,
    source_path: str = f"{DATA_VOLUME_BASE}/customers.csv",
) -> DataFrame:
    """Read customers CSV from the medallion volume and write bronze_customers."""
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
        .saveAsTable("workspace.bronze.bronze_customers")
    )

    return bronze_df


def ingest_orders(
    spark: SparkSession,
    source_path: str = f"{DATA_VOLUME_BASE}/orders.csv",
) -> DataFrame:
    """Read orders CSV from the medallion volume and write bronze_orders."""
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
        .saveAsTable("workspace.bronze.bronze_orders")
    )

    return bronze_df


def ingest_products(
    spark: SparkSession,
    source_path: str = f"{DATA_VOLUME_BASE}/products.csv",
) -> DataFrame:
    """Read products CSV from the medallion volume and write bronze_products."""
    products_df: DataFrame = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(source_path)
    )

    bronze_df: DataFrame = products_df.withColumn(
        "_ingested_at", F.current_timestamp()
    ).withColumn("_source_file", F.col("_metadata.file_path"))

    (
        bronze_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable("workspace.bronze.bronze_products")
    )

    return bronze_df
