"""Silver-layer business logic quality checks."""

from __future__ import annotations

from pyspark.sql import Column
from pyspark.sql.functions import col, lit, when


def check_order_payment_dates(
    order_date_col: str,
    payment_date_col: str,
    error_tag: str,
) -> Column:
    """Return an error tag when payment occurs before the order date.

    Args:
        order_date_col: Order date column to validate against.
        payment_date_col: Payment date column to validate.
        error_tag: DQ error code/message to emit for invalid payment timing.

    Returns:
        A PySpark column expression suitable for building `dq_errors` arrays.
    """
    return when(
        col(payment_date_col).isNotNull() & (col(payment_date_col) < col(order_date_col)),
        lit(error_tag),
    )
