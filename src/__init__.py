"""Databricks Medallion Pipeline — top-level Python package.

This package implements an end-to-end e-commerce analytics pipeline on
Databricks / Delta Lake using the Medallion Architecture:

    Bronze  — lossless CSV ingest with audit metadata
    Silver  — soft-quarantine data quality with dq_errors flagging
    Gold    — PASS-only analytical marts and aggregations
    Dashboard — BI-ready SQL queries against gold tables

Subpackages:
    src.bronze           Raw ingestion modules and Databricks notebooks
    src.silver           Modular DQ check functions and silver orchestrator
    src.gold             SQL mart definitions and gold orchestrator
    src.dashboard        Dashboard queries and execution helpers
    src.data_generation  Synthetic CSV generator with intentional DQ defects

Usage (local):
    python src/data_generation/generate_sample_data.py
    pytest tests/

Usage (Databricks):
    databricks jobs submit --json @conf/bronze_ingest_all_run.json --profile community

Architecture rules are defined in `.cursorrules` and
`tool-specific/cursor-workflow/spec.md`.
"""

from __future__ import annotations

__all__: list[str] = []
