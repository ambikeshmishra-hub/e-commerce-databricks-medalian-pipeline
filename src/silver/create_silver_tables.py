"""Create silver Delta tables by applying modular DQ checks to bronze sources."""

from __future__ import annotations

import os
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    array,
    col,
    count,
    filter as array_filter,
    lit,
    size,
    sum as spark_sum,
    when,
)

from src.silver import (
    check_completeness,
    check_foreign_key,
    check_numeric_positive,
    check_order_payment_dates,
    check_uniqueness,
    flag_duplicates,
    flag_invalid_fk,
)

BRONZE_ORDERS_TABLE = "bronze_orders"
BRONZE_CUSTOMERS_TABLE = "bronze_customers"
BRONZE_PRODUCTS_TABLE = "bronze_products"
SILVER_ORDERS_TABLE = "silver_orders"


@dataclass(frozen=True)
class DqMetricsSummary:
    """Row-level data quality summary for a silver table."""

    total_rows: int
    passed_rows: int
    quarantined_rows: int

    @property
    def passed_pct(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.passed_rows / self.total_rows) * 100

    @property
    def quarantined_pct(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.quarantined_rows / self.total_rows) * 100


def _resolve_table_name(table_name: str) -> str:
    """Return a Unity Catalog table name when running on Databricks."""
    if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
        return table_name

    if table_name.startswith("workspace."):
        return table_name

    if table_name.startswith("bronze_"):
        return f"workspace.bronze.{table_name}"
    if table_name.startswith("silver_"):
        return f"workspace.silver.{table_name}"

    return table_name


def _apply_orders_dq_checks(
    orders_df: DataFrame,
    customers_df: DataFrame,
    products_df: DataFrame,
) -> DataFrame:
    """Apply silver DQ modules 01–05 to bronze orders."""
    orders_with_counts = flag_duplicates(orders_df, id_col="order_id")
    orders_with_customer_fk = check_foreign_key(
        orders_with_counts,
        customers_df,
        fk_col="customer_id",
        parent_pk_col="customer_id",
        alias_col="matched_customer_id",
    )
    orders_with_fks = check_foreign_key(
        orders_with_customer_fk,
        products_df,
        fk_col="product_id",
        parent_pk_col="product_id",
        alias_col="matched_product_id",
    )

    return (
        orders_with_fks.withColumn(
            "dq_errors",
            array_filter(
                array(
                    check_completeness("customer_id", "NULL_CUSTOMER_ID"),
                    check_completeness("product_id", "NULL_PRODUCT_ID"),
                    check_uniqueness("row_occurrence_count", "DUPLICATE_ORDER_ID"),
                    check_numeric_positive("quantity", "NON_POSITIVE_QUANTITY"),
                    check_numeric_positive("unit_price", "NON_POSITIVE_UNIT_PRICE"),
                    check_numeric_positive("total_amount", "NON_POSITIVE_TOTAL_AMOUNT"),
                    flag_invalid_fk(
                        "matched_customer_id",
                        "customer_id",
                        "INVALID_CUSTOMER_ID_FK",
                    ),
                    flag_invalid_fk(
                        "matched_product_id",
                        "product_id",
                        "INVALID_PRODUCT_ID_FK",
                    ),
                    check_order_payment_dates(
                        "order_date",
                        "payment_date",
                        "PAYMENT_BEFORE_ORDER_DATE",
                    ),
                ),
                lambda error: error.isNotNull(),
            ),
        )
        .withColumn(
            "quality_check_result",
            when(size(col("dq_errors")) == 0, lit("PASS")).otherwise(lit("FAIL")),
        )
        .drop("row_occurrence_count", "matched_customer_id", "matched_product_id")
    )


def _calculate_dq_metrics(silver_df: DataFrame) -> DqMetricsSummary:
    """Aggregate pass/fail counts for the silver orders table."""
    metrics_row = silver_df.agg(
        count(lit(1)).alias("total_rows"),
        spark_sum(when(col("quality_check_result") == "PASS", 1).otherwise(0)).alias(
            "passed_rows"
        ),
    ).first()

    if metrics_row is None:
        return DqMetricsSummary(total_rows=0, passed_rows=0, quarantined_rows=0)

    total_rows = int(metrics_row["total_rows"])
    passed_rows = int(metrics_row["passed_rows"])
    return DqMetricsSummary(
        total_rows=total_rows,
        passed_rows=passed_rows,
        quarantined_rows=total_rows - passed_rows,
    )


def print_dq_metrics_summary(summary: DqMetricsSummary) -> None:
    """Print a human-readable data quality metrics summary to stdout."""
    print("=" * 60)
    print("Data Quality Metrics Summary — silver_orders")
    print("=" * 60)
    print(f"Total rows processed:      {summary.total_rows:>10,}")
    print(
        f"Passed rows:               {summary.passed_rows:>10,} "
        f"({summary.passed_pct:>6.2f}%)"
    )
    print(
        f"Quarantined bad rows:      {summary.quarantined_rows:>10,} "
        f"({summary.quarantined_pct:>6.2f}%)"
    )
    print("=" * 60)


def create_silver_orders(spark: SparkSession) -> DataFrame:
    """Read bronze tables, apply DQ checks, and write `silver_orders`."""
    orders_df = spark.table(_resolve_table_name(BRONZE_ORDERS_TABLE))
    customers_df = spark.table(_resolve_table_name(BRONZE_CUSTOMERS_TABLE))
    products_df = spark.table(_resolve_table_name(BRONZE_PRODUCTS_TABLE))

    silver_orders_df = _apply_orders_dq_checks(orders_df, customers_df, products_df)

    silver_table = _resolve_table_name(SILVER_ORDERS_TABLE)
    (
        silver_orders_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(silver_table)
    )

    summary = _calculate_dq_metrics(silver_orders_df)
    print_dq_metrics_summary(summary)

    return silver_orders_df


def run_silver_pipeline(spark: SparkSession) -> DataFrame:
    """Create the silver schema (if needed) and build silver tables."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.silver")

    print("[silver] Starting silver_orders creation.")
    silver_orders_df = create_silver_orders(spark)
    print("[silver] Pipeline complete.")
    return silver_orders_df


def _build_spark_session() -> SparkSession:
    """Create a Spark session with Delta Lake catalog support."""
    return (
        SparkSession.builder.appName("create_silver_tables")
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
    run_silver_pipeline(spark_session)
