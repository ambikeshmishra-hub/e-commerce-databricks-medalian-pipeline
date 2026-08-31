"""Orchestrate all bronze CSV ingestions into Delta Lake tables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, List

from pyspark.sql import DataFrame, SparkSession

from src.bronze import ingest_customers, ingest_orders, ingest_products


@dataclass(frozen=True)
class IngestResult:
    """Summary of a single bronze ingestion step."""

    dataset: str
    row_count: int


def _build_spark_session() -> SparkSession:
    """Create a Spark session with Delta Lake catalog support."""
    return (
        SparkSession.builder.appName("bronze_ingest_all")
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


def _run_ingest(
    dataset: str,
    ingest_fn: Callable[[SparkSession], DataFrame],
    spark: SparkSession,
) -> IngestResult:
    """Execute one ingest function and log pipeline progress."""
    print(f"[bronze] Starting ingest: {dataset}")
    bronze_df = ingest_fn(spark)
    row_count = bronze_df.count()
    print(f"[bronze] Completed ingest: {dataset} -> {row_count:,} rows")
    return IngestResult(dataset=dataset, row_count=row_count)


def run_bronze_ingestion(spark: SparkSession) -> List[IngestResult]:
    """Run customers, orders, and products bronze ingestions sequentially."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.bronze")

    ingest_steps = [
        ("customers", ingest_customers),
        ("orders", ingest_orders),
        ("products", ingest_products),
    ]

    results: List[IngestResult] = []
    for dataset, ingest_fn in ingest_steps:
        results.append(_run_ingest(dataset=dataset, ingest_fn=ingest_fn, spark=spark))

    print("[bronze] Pipeline complete.")
    for result in results:
        print(f"  - {result.dataset}: {result.row_count:,} rows")

    return results


if __name__ == "__main__":
    spark_session = _build_spark_session()
    run_bronze_ingestion(spark_session)
