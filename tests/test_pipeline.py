"""Pipeline integration tests for bronze, silver, and gold layers."""

from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Generated dataset contains 50,000 orders (see NUM_ORDERS in generate_sample_data.py).
BRONZE_ORDERS_MIN_ROWS = 50_000
MIN_QUARANTINED_ROWS = 400
VALID_BEHAVIORAL_SEGMENTS = frozenset(
    {"High-Value", "Repeat", "One-Time", "Inactive"}
)


def _resolve_table(table_name: str) -> str:
    """Return Unity Catalog table names when running on Databricks."""
    if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
        return table_name

    if table_name.startswith("workspace."):
        return table_name

    if table_name.startswith("bronze_"):
        return f"workspace.bronze.{table_name}"
    if table_name.startswith("silver_"):
        return f"workspace.silver.{table_name}"
    if table_name.startswith("gold_"):
        return f"workspace.gold.{table_name}"

    return table_name


def _derived_segment_type_column():
    """Mirror gold_customer_segmentation segment assignment rules."""
    return (
        F.when(F.col("total_revenue") > 3000, F.lit("High-Value"))
        .when(F.col("total_orders") > 5, F.lit("Repeat"))
        .when(F.col("total_orders") == 1, F.lit("One-Time"))
        .otherwise(F.lit("Inactive"))
    )


def test_bronze_ingestion_counts(spark: SparkSession) -> None:
    """Validate bronze ingestion row volumes and audit metadata columns."""
    bronze_orders = spark.table(_resolve_table("bronze_orders"))
    bronze_customers = spark.table(_resolve_table("bronze_customers"))
    bronze_products = spark.table(_resolve_table("bronze_products"))

    orders_count = bronze_orders.count()
    customers_count = bronze_customers.count()
    products_count = bronze_products.count()

    assert orders_count >= BRONZE_ORDERS_MIN_ROWS, (
        f"Expected bronze_orders to contain at least {BRONZE_ORDERS_MIN_ROWS:,} rows, "
        f"but found {orders_count:,}."
    )
    assert customers_count > 0, (
        f"Expected bronze_customers to be non-empty, but found {customers_count:,} rows."
    )
    assert products_count > 0, (
        f"Expected bronze_products to be non-empty, but found {products_count:,} rows."
    )

    for table_name, bronze_df in (
        ("bronze_orders", bronze_orders),
        ("bronze_customers", bronze_customers),
        ("bronze_products", bronze_products),
    ):
        schema_fields = {field.name for field in bronze_df.schema.fields}
        assert "_ingested_at" in schema_fields, (
            f"Expected {table_name} to include metadata column '_ingested_at'."
        )
        assert "_source_file" in schema_fields, (
            f"Expected {table_name} to include metadata column '_source_file'."
        )

        null_metadata_count = bronze_df.filter(
            F.col("_ingested_at").isNull() | F.col("_source_file").isNull()
        ).count()
        assert null_metadata_count == 0, (
            f"Expected {table_name} metadata columns '_ingested_at' and '_source_file' "
            f"to be populated for every row, but found {null_metadata_count:,} null values."
        )


def test_silver_soft_quarantine_anomaly_detection(spark: SparkSession) -> None:
    """Validate silver soft-quarantine preserves all rows and flags anomalies."""
    bronze_orders = spark.table(_resolve_table("bronze_orders"))
    silver_orders = spark.table(_resolve_table("silver_orders"))

    bronze_count = bronze_orders.count()
    silver_count = silver_orders.count()
    assert silver_count == bronze_count, (
        "Silver soft-quarantine must not drop rows. "
        f"bronze_orders={bronze_count:,}, silver_orders={silver_count:,}."
    )

    quarantined_count = silver_orders.filter(
        F.col("quality_check_result") == "FAIL"
    ).count()
    pass_count = silver_orders.filter(
        F.col("quality_check_result") == "PASS"
    ).count()
    assert pass_count > 0, (
        f"Expected silver_orders to contain PASS rows for gold layer sourcing, "
        f"but found {pass_count:,} PASS rows."
    )
    assert quarantined_count > MIN_QUARANTINED_ROWS, (
        "Expected silver_orders to quarantine more than "
        f"{MIN_QUARANTINED_ROWS:,} intentionally bad rows, but found "
        f"{quarantined_count:,} FAIL rows."
    )

    invalid_pass_count = silver_orders.filter(
        (F.col("quality_check_result") == "PASS")
        & (F.size(F.col("dq_errors")) > 0)
    ).count()
    assert invalid_pass_count == 0, (
        "PASS rows must have an empty dq_errors array. Found "
        f"{invalid_pass_count:,} PASS rows with non-empty dq_errors."
    )


def test_gold_layer_integrity(spark: SparkSession) -> None:
    """Validate gold mart population, revenue sanity, and segment assignment."""
    gold_sales_by_product = spark.table(_resolve_table("gold_sales_by_product"))
    gold_revenue_by_customer = spark.table(
        _resolve_table("gold_revenue_by_customer")
    )

    sales_count = gold_sales_by_product.count()
    revenue_count = gold_revenue_by_customer.count()
    assert sales_count > 0, (
        f"Expected gold_sales_by_product to be non-empty, but found {sales_count:,} rows."
    )
    assert revenue_count > 0, (
        "Expected gold_revenue_by_customer to be non-empty, but found "
        f"{revenue_count:,} rows."
    )

    invalid_sales_revenue_count = gold_sales_by_product.filter(
        F.col("total_revenue").isNull() | (F.col("total_revenue") <= 0)
    ).count()
    assert invalid_sales_revenue_count == 0, (
        "gold_sales_by_product must not contain null, zero, or negative total_revenue "
        f"values. Found {invalid_sales_revenue_count:,} invalid rows."
    )

    invalid_customer_revenue_count = gold_revenue_by_customer.filter(
        F.col("total_revenue").isNull() | (F.col("total_revenue") <= 0)
    ).count()
    assert invalid_customer_revenue_count == 0, (
        "gold_revenue_by_customer must not contain null, zero, or negative total_revenue "
        f"values. Found {invalid_customer_revenue_count:,} invalid rows."
    )

    invalid_segment_count = (
        gold_revenue_by_customer.withColumn(
            "derived_segment_type", _derived_segment_type_column()
        )
        .filter(~F.col("derived_segment_type").isin(*VALID_BEHAVIORAL_SEGMENTS))
        .count()
    )
    assert invalid_segment_count == 0, (
        "Every customer in gold_revenue_by_customer must map to a valid behavioral "
        f"segment {sorted(VALID_BEHAVIORAL_SEGMENTS)}. Found "
        f"{invalid_segment_count:,} rows with invalid derived segments."
    )


def run_pipeline_tests(spark: SparkSession) -> None:
    """Execute all pipeline tests sequentially (for Databricks notebooks)."""
    print("[tests] Running test_bronze_ingestion_counts")
    test_bronze_ingestion_counts(spark)
    print("[tests] PASSED test_bronze_ingestion_counts")

    print("[tests] Running test_silver_soft_quarantine_anomaly_detection")
    test_silver_soft_quarantine_anomaly_detection(spark)
    print("[tests] PASSED test_silver_soft_quarantine_anomaly_detection")

    print("[tests] Running test_gold_layer_integrity")
    test_gold_layer_integrity(spark)
    print("[tests] PASSED test_gold_layer_integrity")

    print("[tests] All pipeline integrity tests passed.")
