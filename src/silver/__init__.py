"""Silver-layer data quality modules."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_SILVER_DIR = Path(__file__).resolve().parent


def _load_module(module_file: str, module_name: str):
    spec = spec_from_file_location(module_name, _SILVER_DIR / module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load silver module: {module_file}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_completeness = _load_module("01_quality_completeness.py", "quality_completeness")
check_completeness = _completeness.check_completeness

_uniqueness = _load_module("02_quality_uniqueness.py", "quality_uniqueness")
flag_duplicates = _uniqueness.flag_duplicates
check_uniqueness = _uniqueness.check_uniqueness

_type_validation = _load_module("03_quality_type_validation.py", "quality_type_validation")
check_numeric_positive = _type_validation.check_numeric_positive

_referential_integrity = _load_module(
    "04_quality_referential_integrity.py", "quality_referential_integrity"
)
check_foreign_key = _referential_integrity.check_foreign_key
flag_invalid_fk = _referential_integrity.flag_invalid_fk

_business_logic = _load_module("05_quality_business_logic.py", "quality_business_logic")
check_order_payment_dates = _business_logic.check_order_payment_dates

__all__ = [
    "check_completeness",
    "flag_duplicates",
    "check_uniqueness",
    "check_numeric_positive",
    "check_foreign_key",
    "flag_invalid_fk",
    "check_order_payment_dates",
]
