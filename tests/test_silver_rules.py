"""Unit tests for silver-layer DQ helper functions (modules 01–05)."""

from __future__ import annotations

from datetime import date

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.silver import (
    check_completeness,
    check_foreign_key,
    check_order_payment_dates,
    check_uniqueness,
    flag_duplicates,
    flag_invalid_fk,
)


def test_completeness_check(spark: SparkSession) -> None:
    """Verify check_completeness tags only null values."""
    source_df = spark.createDataFrame(
        [(1, "alice@example.com"), (2, None), (3, "bob@example.com")],
        ["customer_id", "email"],
    )

    results = source_df.select(
        "customer_id",
        check_completeness("email", "NULL_EMAIL").alias("completeness_error"),
    ).collect()
    errors_by_id = {row["customer_id"]: row["completeness_error"] for row in results}

    assert errors_by_id[1] is None, (
        "Non-null email values must not produce a completeness error tag."
    )
    assert errors_by_id[2] == "NULL_EMAIL", (
        "Null email values must produce the NULL_EMAIL completeness error tag."
    )
    assert errors_by_id[3] is None, (
        "Non-null email values must not produce a completeness error tag."
    )


def test_uniqueness_check(spark: SparkSession) -> None:
    """Verify duplicate identifiers are flagged without dropping rows."""
    source_df = spark.createDataFrame(
        [(101, "row-a"), (101, "row-b"), (102, "row-c")],
        ["order_id", "note"],
    )

    uniqueness_df = flag_duplicates(source_df, id_col="order_id").select(
        "order_id",
        "row_occurrence_count",
        check_uniqueness("row_occurrence_count", "DUPLICATE_ORDER_ID").alias(
            "uniqueness_error"
        ),
    )

    assert uniqueness_df.count() == source_df.count(), (
        "flag_duplicates must retain every input row when detecting duplicate keys."
    )

    duplicate_errors = [
        row["uniqueness_error"]
        for row in uniqueness_df.filter(F.col("order_id") == 101).collect()
    ]
    unique_errors = uniqueness_df.filter(F.col("order_id") == 102).collect()

    assert len(duplicate_errors) == 2, (
        "Expected exactly two rows for duplicate order_id 101."
    )
    assert all(error == "DUPLICATE_ORDER_ID" for error in duplicate_errors), (
        "Duplicate order_id rows must be tagged with DUPLICATE_ORDER_ID."
    )
    assert unique_errors[0]["uniqueness_error"] is None, (
        "Unique order_id rows must not produce a uniqueness error tag."
    )


def test_referential_integrity_check(spark: SparkSession) -> None:
    """Verify orphan foreign keys are retained and flagged."""
    child_df = spark.createDataFrame(
        [(1, 10), (2, 20), (3, 99)],
        ["order_id", "customer_id"],
    )
    parent_df = spark.createDataFrame([(10,), (20,)], ["customer_id"])

    joined_df = check_foreign_key(
        child_df,
        parent_df,
        fk_col="customer_id",
        parent_pk_col="customer_id",
        alias_col="matched_customer_id",
    )

    assert joined_df.count() == child_df.count(), (
        "check_foreign_key must retain all child rows, including orphan foreign keys."
    )

    integrity_results = joined_df.select(
        "order_id",
        flag_invalid_fk(
            "matched_customer_id", "customer_id", "INVALID_CUSTOMER_ID_FK"
        ).alias("fk_error"),
    ).collect()
    errors_by_order = {row["order_id"]: row["fk_error"] for row in integrity_results}

    assert errors_by_order[1] is None, (
        "Valid foreign keys must not produce an INVALID_CUSTOMER_ID_FK error tag."
    )
    assert errors_by_order[2] is None, (
        "Valid foreign keys must not produce an INVALID_CUSTOMER_ID_FK error tag."
    )
    assert errors_by_order[3] == "INVALID_CUSTOMER_ID_FK", (
        "Orphan foreign keys must produce an INVALID_CUSTOMER_ID_FK error tag."
    )


def test_business_logic_dates(spark: SparkSession) -> None:
    """Verify only premature payment dates are flagged."""
    source_df = spark.createDataFrame(
        [
            (1, date(2024, 1, 10), date(2024, 1, 12)),
            (2, date(2024, 1, 10), date(2024, 1, 9)),
            (3, date(2024, 1, 10), None),
            (4, date(2024, 1, 10), date(2024, 1, 10)),
        ],
        ["order_id", "order_date", "payment_date"],
    )

    results = source_df.select(
        "order_id",
        check_order_payment_dates(
            "order_date", "payment_date", "PAYMENT_BEFORE_ORDER_DATE"
        ).alias("payment_error"),
    ).collect()
    errors_by_order = {row["order_id"]: row["payment_error"] for row in results}

    assert errors_by_order[1] is None, (
        "Payments on or after the order date must not be flagged."
    )
    assert errors_by_order[2] == "PAYMENT_BEFORE_ORDER_DATE", (
        "Payments before the order date must be flagged with PAYMENT_BEFORE_ORDER_DATE."
    )
    assert errors_by_order[3] is None, (
        "Null payment dates must not be flagged by the business-logic date check."
    )
    assert errors_by_order[4] is None, (
        "Payments on the same day as the order date must not be flagged."
    )


def run_silver_rules_tests(spark: SparkSession) -> None:
    """Execute all silver helper unit tests sequentially (for Databricks notebooks)."""
    test_functions = (
        test_completeness_check,
        test_uniqueness_check,
        test_referential_integrity_check,
        test_business_logic_dates,
    )

    print("[tests] Starting silver rules unit tests.")
    for test_function in test_functions:
        print(f"[tests] Running {test_function.__name__}")
        test_function(spark)
        print(f"[tests] PASSED {test_function.__name__}")

    print("[tests] All silver rules unit tests passed.")
