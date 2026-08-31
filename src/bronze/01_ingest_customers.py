"""Bronze-layer ingestion for the customers CSV source."""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

BRONZE_TABLE_NAME = "bronze_customers"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_source_path(source_path: str) -> str:
    """Return an absolute path when a relative project path is provided."""
    path = Path(source_path)
    if path.is_absolute():
        return str(path)
    return str(PROJECT_ROOT / path)


def ingest_customers(
    spark: SparkSession,
    source_path: str = "data/customers.csv",
) -> DataFrame:
    """Read customers CSV, append audit metadata, and write the bronze Delta table.

    Args:
        spark: Active Spark session configured for Delta Lake.
        source_path: Path to the customers CSV file (relative to project root or absolute).

    Returns:
        The bronze DataFrame written to Delta (including metadata columns).
    """
    resolved_path = _resolve_source_path(source_path)

    customers_df: DataFrame = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(resolved_path)
    )

    bronze_df: DataFrame = customers_df.withColumn(
        "_ingested_at", F.current_timestamp()
    ).withColumn("_source_file", F.input_file_name())

    (
        bronze_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(BRONZE_TABLE_NAME)
    )

    return bronze_df


def _build_spark_session() -> SparkSession:
    """Create a local Spark session with Delta Lake support for standalone runs."""
    return (
        SparkSession.builder.appName("bronze_ingest_customers")
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
    bronze_customers_df = ingest_customers(spark_session)
    print(f"Wrote Delta table: {BRONZE_TABLE_NAME}")
    print(f"Row count: {bronze_customers_df.count():,}")
