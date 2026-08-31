"""Execute all gold SQL marts and materialize Delta tables in Databricks."""

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import SparkSession

_GOLD_DIR = Path(__file__).resolve().parent
_DATABRICKS_GOLD_DIR = "/Workspace/Shared/medallion-pipeline/src/gold"

GOLD_SQL_FILES: tuple[tuple[str, str], ...] = (
    ("01_sales_by_product.sql", "workspace.gold.gold_sales_by_product"),
    ("02_revenue_by_customer.sql", "workspace.gold.gold_revenue_by_customer"),
    ("03_daily_weekly_trends.sql", "workspace.gold.gold_daily_weekly_trends"),
    ("04_customer_segmentation.sql", "workspace.gold.gold_customer_segmentation"),
)


def _resolve_sql_filepath(filename: str) -> str:
    """Return the local or Databricks workspace path for a gold SQL file."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        return f"{_DATABRICKS_GOLD_DIR}/{filename}"
    return str(_GOLD_DIR / filename)


def execute_sql_file(spark: SparkSession, filepath: str) -> None:
    """Read a SQL file from disk and execute it via Spark SQL.

    Args:
        spark: Active Spark session.
        filepath: Absolute path to the SQL file to execute.
    """
    with open(filepath, encoding="utf-8") as sql_file:
        query = sql_file.read()
    spark.sql(query)


def run_gold_pipeline(spark: SparkSession) -> None:
    """Materialize all gold analytical tables by executing SQL files sequentially."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.gold")

    print("[gold] Starting gold table materialization pipeline.")

    for sql_filename, table_name in GOLD_SQL_FILES:
        sql_filepath = _resolve_sql_filepath(sql_filename)
        print(f"[gold] Starting materialization: {table_name} ({sql_filename})")
        execute_sql_file(spark, sql_filepath)
        row_count = spark.table(table_name).count()
        print(
            f"[gold] Completed materialization: {table_name} -> {row_count:,} rows"
        )

    print("[gold] Pipeline complete. All four gold tables materialized.")


def _build_spark_session() -> SparkSession:
    """Create a Spark session with Delta Lake catalog support."""
    return (
        SparkSession.builder.appName("create_gold_tables")
        .config(
            "spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension",
        )
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )


if __name__ == "__main__":
    spark_session = _build_spark_session()
    run_gold_pipeline(spark_session)
