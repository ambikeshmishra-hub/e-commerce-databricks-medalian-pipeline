"""Pytest configuration for pipeline integration tests."""

from __future__ import annotations

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Initialize a local PySpark session with Delta Lake catalog support."""
    active_session = SparkSession.getActiveSession()
    if active_session is not None:
        return active_session

    session = (
        SparkSession.builder.master("local[*]")
        .appName("pipeline_tests")
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
    yield session
    session.stop()
