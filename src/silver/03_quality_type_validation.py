"""Silver-layer type validation quality checks."""

from __future__ import annotations

from pyspark.sql import Column
from pyspark.sql.functions import col, expr, lit, when


def check_numeric_positive(column_name: str, error_tag: str) -> Column:
    """Return an error tag when the numeric column is zero or negative.

    Args:
        column_name: Numeric column to validate.
        error_tag: DQ error code/message to emit for non-positive values.

    Returns:
        A PySpark column expression suitable for building `dq_errors` arrays.
    """
    numeric_value = expr(f"try_cast(`{column_name}` AS DOUBLE)")
    return when(numeric_value.isNotNull() & (numeric_value <= 0), lit(error_tag))
