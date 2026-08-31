"""Silver-layer completeness quality checks."""

from __future__ import annotations

from pyspark.sql import Column
from pyspark.sql.functions import col, lit, when


def check_completeness(column_name: str, error_tag: str) -> Column:
    """Return an error tag when the target column is null, otherwise null.

    Args:
        column_name: Column to evaluate for null values.
        error_tag: DQ error code/message to emit when the column is null.

    Returns:
        A PySpark column expression suitable for building `dq_errors` arrays.
    """
    return when(col(column_name).isNull(), lit(error_tag))
