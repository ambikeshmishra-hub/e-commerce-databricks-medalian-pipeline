"""Silver-layer referential integrity quality checks."""

from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql.functions import col, lit, when


def check_foreign_key(
    child_df: DataFrame,
    parent_df: DataFrame,
    fk_col: str,
    parent_pk_col: str,
    alias_col: str,
) -> DataFrame:
    """Join child rows to distinct parent keys without dropping orphan records.

    Args:
        child_df: Child DataFrame containing the foreign key column.
        parent_df: Parent DataFrame containing the primary key column.
        fk_col: Foreign key column on the child DataFrame.
        parent_pk_col: Primary key column on the parent DataFrame.
        alias_col: Output column name for the matched parent key.

    Returns:
        Child DataFrame left-joined to distinct parent primary keys.
    """
    parent_keys = parent_df.select(col(parent_pk_col).alias(alias_col)).distinct()
    return child_df.join(parent_keys, col(fk_col) == col(alias_col), "left")


def flag_invalid_fk(alias_col: str, fk_col: str, error_tag: str) -> Column:
    """Return an error tag when a non-null foreign key has no parent match.

    Args:
        alias_col: Parent key column produced by `check_foreign_key`.
        fk_col: Foreign key column on the child DataFrame.
        error_tag: DQ error code/message to emit for orphan foreign keys.

    Returns:
        A PySpark column expression suitable for building `dq_errors` arrays.
    """
    return when(col(fk_col).isNotNull() & col(alias_col).isNull(), lit(error_tag))
