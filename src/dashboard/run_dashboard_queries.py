"""Execute dashboard BI tile queries from the shared SQL file."""

from __future__ import annotations

import os
import re
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

_DASHBOARD_DIR = Path(__file__).resolve().parent
_DATABRICKS_DASHBOARD_DIR = "/Workspace/Shared/medallion-pipeline/src/dashboard"
_DASHBOARD_SQL_FILE = "dashboard_queries.sql"
_TILE_HEADER_PATTERN = re.compile(
    r"-- Tile (\d+) Query \(([^)]+)\): ([^\n]+)\n",
    re.IGNORECASE,
)


def _resolve_sql_filepath() -> str:
    """Return the local or Databricks workspace path for dashboard SQL."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        return f"{_DATABRICKS_DASHBOARD_DIR}/{_DASHBOARD_SQL_FILE}"
    return str(_DASHBOARD_DIR / _DASHBOARD_SQL_FILE)


def _parse_dashboard_queries(sql_text: str) -> list[tuple[int, str, str, str]]:
    """Parse tile metadata and SELECT statements from the dashboard SQL file."""
    matches = list(_TILE_HEADER_PATTERN.finditer(sql_text))
    if not matches:
        raise ValueError("No dashboard tile queries found in SQL file.")

    tiles: list[tuple[int, str, str, str]] = []
    for index, match in enumerate(matches):
        tile_number = int(match.group(1))
        chart_type = match.group(2).strip()
        title = match.group(3).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql_text)
        query = sql_text[start:end].strip().rstrip(";")
        tiles.append((tile_number, chart_type, title, query))

    return tiles


def run_dashboard_queries(spark: SparkSession) -> list[tuple[int, str, str, DataFrame]]:
    """Execute all dashboard tile queries and return result DataFrames."""
    sql_filepath = _resolve_sql_filepath()
    with open(sql_filepath, encoding="utf-8") as sql_file:
        sql_text = sql_file.read()

    tiles = _parse_dashboard_queries(sql_text)
    results: list[tuple[int, str, str, DataFrame]] = []

    print("[dashboard] Starting BI tile query execution.")
    for tile_number, chart_type, title, query in tiles:
        print(
            f"[dashboard] Executing Tile {tile_number} ({chart_type}): {title}"
        )
        result_df = spark.sql(query)
        row_count = result_df.count()
        print(f"[dashboard] Tile {tile_number} complete -> {row_count:,} rows")
        result_df.show(truncate=False)
        results.append((tile_number, chart_type, title, result_df))

    print("[dashboard] All dashboard tile queries executed successfully.")
    return results
