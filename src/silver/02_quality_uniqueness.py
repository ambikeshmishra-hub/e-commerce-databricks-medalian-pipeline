"""Silver-layer uniqueness quality checks."""

from __future__ import annotations

from pyspark.sql import Column, DataFrame, Window
from pyspark.sql.functions import col, count, lit, when


def flag_duplicates(
    df: DataFrame,
    id_col: str,
    count_col_name: str = "row_occurrence_count",
) -> DataFrame:
    """Add an occurrence count per identifier without grouping or dropping rows.

    Args:
        df: Input DataFrame to evaluate.
        id_col: Identifier column used to detect duplicate keys.
        count_col_name: Name of the output count column.

    Returns:
        DataFrame with an added occurrence count column per row.
    """
    duplicate_window = Window.partitionBy(id_col)
    return df.withColumn(count_col_name, count(col(id_col)).over(duplicate_window))


def check_uniqueness(count_col_name: str, error_tag: str) -> Column:
    """Return an error tag when the occurrence count indicates a duplicate key.

    Args:
        count_col_name: Column containing per-key occurrence counts.
        error_tag: DQ error code/message to emit for duplicate keys.

    Returns:
        A PySpark column expression suitable for building `dq_errors` arrays.
    """
    return when(col(count_col_name) > 1, lit(error_tag))
