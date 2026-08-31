"""Bronze ingestion package exports."""

from __future__ import annotations

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable

_BRONZE_DIR = Path(__file__).resolve().parent


def _load_ingest_function(module_file: str, function_name: str) -> Callable[..., Any]:
    """Load an ingest function from a numbered bronze module file."""
    spec = spec_from_file_location(function_name, _BRONZE_DIR / module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load bronze module: {module_file}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)


if "DATABRICKS_RUNTIME_VERSION" in os.environ:
    from src.bronze.databricks_ingest import (  # noqa: F401
        ingest_customers,
        ingest_orders,
        ingest_products,
    )
else:
    ingest_customers = _load_ingest_function("01_ingest_customers.py", "ingest_customers")
    ingest_orders = _load_ingest_function("02_ingest_orders.py", "ingest_orders")
    ingest_products = _load_ingest_function("03_ingest_products.py", "ingest_products")

__all__ = ["ingest_customers", "ingest_orders", "ingest_products"]
