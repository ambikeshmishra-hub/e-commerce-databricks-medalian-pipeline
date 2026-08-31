"""Create and publish the E-Commerce Gold Analytics Lakeview dashboard."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from src.dashboard.run_dashboard_queries import run_dashboard_queries

DASHBOARD_DISPLAY_NAME = "E-Commerce Gold Analytics"
DASHBOARD_PARENT_PATH = "/Shared/medallion-pipeline/dashboard"
DEFAULT_WAREHOUSE_ID = "30007f4d2e8531c0"


@dataclass(frozen=True)
class PublishedDashboard:
    """Result metadata after Lakeview dashboard publish."""

    dashboard_id: str
    display_name: str
    workspace_url: str
    dashboard_url: str
    warehouse_id: str


def _resolve_warehouse_id() -> str:
    """Return SQL warehouse ID from env or default."""
    return os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", DEFAULT_WAREHOUSE_ID)


def _resolve_api_credentials() -> tuple[str, str]:
    """Resolve Databricks host and token for REST API calls."""
    host = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
    token = os.environ.get("DATABRICKS_TOKEN", "")

    if host and token:
        return host, token

    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("Active Spark session required to publish dashboard.")

        dbutils = DBUtils(spark)
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        api_url = context.apiUrl().get()
        api_token = context.apiToken().get()
        if not api_url or not api_token:
            raise RuntimeError("Unable to resolve Databricks notebook API credentials.")
        return api_url.rstrip("/"), api_token

    raise RuntimeError(
        "Set DATABRICKS_HOST and DATABRICKS_TOKEN, or run inside a Databricks notebook."
    )


def _api_request(
    method: str,
    path: str,
    host: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a Databricks REST API request."""
    url = f"{host}{path}"
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Databricks API {method} {path} failed: {exc.code} {detail}") from exc


def _list_dashboards(host: str, token: str) -> list[dict[str, Any]]:
    """List active Lakeview dashboards."""
    response = _api_request("GET", "/api/2.0/lakeview/dashboards", host, token)
    if isinstance(response, dict):
        dashboards = response.get("dashboards")
        if isinstance(dashboards, list):
            return dashboards
    return []


def _delete_dashboard(dashboard_id: str, host: str, token: str) -> None:
    """Trash an existing dashboard by ID."""
    _api_request("DELETE", f"/api/2.0/lakeview/dashboards/{dashboard_id}", host, token)


def _build_widget(
    widget_name: str,
    dataset_name: str,
    title: str,
    widget_type: str,
    x_field: str,
    y_field: str,
    color_field: str | None,
    position: dict[str, int],
) -> dict[str, Any]:
    """Build a single Lakeview dashboard widget layout entry."""
    quantitative_fields = {"total_revenue", "customer_count"}

    def _scale(field_name: str) -> dict[str, str]:
        scale_type = "quantitative" if field_name in quantitative_fields else "categorical"
        return {"type": scale_type}

    encodings: dict[str, Any] = {
        "x": {
            "fieldName": x_field,
            "displayName": x_field,
            "scale": _scale(x_field),
        },
        "y": {
            "fieldName": y_field,
            "displayName": y_field,
            "scale": _scale(y_field),
        },
    }
    if color_field:
        encodings["color"] = {
            "fieldName": color_field,
            "displayName": color_field,
            "scale": {"type": "categorical"},
        }

    return {
        "widget": {
            "name": widget_name,
            "queries": [
                {
                    "name": "main_query",
                    "query": {"datasetName": dataset_name, "disaggregated": True},
                }
            ],
            "spec": {
                "version": 3,
                "widgetType": widget_type,
                "encodings": encodings,
                "frame": {"showTitle": True, "title": title},
            },
        },
        "position": position,
    }


def build_serialized_dashboard() -> str:
    """Build Lakeview serialized dashboard JSON for three gold BI tiles."""
    dataset_top_products = str(uuid.uuid4())
    dataset_revenue_dist = str(uuid.uuid4())
    dataset_segmentation = str(uuid.uuid4())

    sql_top_products = (
        "SELECT product_name, category, total_revenue "
        "FROM workspace.gold.gold_sales_by_product "
        "ORDER BY total_revenue DESC LIMIT 10"
    )
    sql_revenue_dist = (
        "SELECT CASE WHEN total_revenue <= 500 THEN '0 - 500' "
        "WHEN total_revenue <= 1500 THEN '500 - 1500' "
        "WHEN total_revenue <= 3000 THEN '1501 - 3000' "
        "ELSE '3000+' END AS revenue_bucket, COUNT(*) AS customer_count "
        "FROM workspace.gold.gold_revenue_by_customer GROUP BY 1 "
        "ORDER BY CASE revenue_bucket "
        "WHEN '0 - 500' THEN 1 WHEN '500 - 1500' THEN 2 "
        "WHEN '1501 - 3000' THEN 3 ELSE 4 END"
    )
    sql_segmentation = (
        "SELECT segment_type, customer_count, total_revenue "
        "FROM workspace.gold.gold_customer_segmentation "
        "ORDER BY CASE segment_type "
        "WHEN 'High-Value' THEN 1 WHEN 'Repeat' THEN 2 "
        "WHEN 'One-Time' THEN 3 WHEN 'Inactive' THEN 4 END"
    )

    dashboard = {
        "datasets": [
            {
                "name": dataset_top_products,
                "displayName": "tile1_top_products",
                "queryLines": [sql_top_products],
            },
            {
                "name": dataset_revenue_dist,
                "displayName": "tile2_revenue_distribution",
                "queryLines": [sql_revenue_dist],
            },
            {
                "name": dataset_segmentation,
                "displayName": "tile3_segmentation",
                "queryLines": [sql_segmentation],
            },
        ],
        "pages": [
            {
                "name": str(uuid.uuid4()),
                "displayName": DASHBOARD_DISPLAY_NAME,
                "pageType": "PAGE_TYPE_CANVAS",
                "layout": [
                    _build_widget(
                        str(uuid.uuid4()),
                        dataset_top_products,
                        "Top 10 Products by Revenue",
                        "bar",
                        "total_revenue",
                        "product_name",
                        "category",
                        {"x": 0, "y": 0, "width": 6, "height": 8},
                    ),
                    _build_widget(
                        str(uuid.uuid4()),
                        dataset_revenue_dist,
                        "Customer Revenue Distribution",
                        "bar",
                        "revenue_bucket",
                        "customer_count",
                        None,
                        {"x": 6, "y": 0, "width": 6, "height": 8},
                    ),
                    _build_widget(
                        str(uuid.uuid4()),
                        dataset_segmentation,
                        "Customer Segmentation Breakdown",
                        "pie",
                        "segment_type",
                        "customer_count",
                        None,
                        {"x": 0, "y": 8, "width": 12, "height": 8},
                    ),
                ],
            }
        ],
        "uiSettings": {"theme": {"widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"}},
    }
    return json.dumps(dashboard)


def publish_gold_dashboard(
    spark: Any | None = None,
    *,
    validate_queries: bool = True,
    warehouse_id: str | None = None,
) -> PublishedDashboard:
    """Validate gold tile queries, create/update Lakeview dashboard, and publish it."""
    if validate_queries:
        if spark is None:
            from pyspark.sql import SparkSession

            spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("Spark session required to validate dashboard queries.")
        print("[dashboard] Validating gold tile queries before publish.")
        run_dashboard_queries(spark)

    host, token = _resolve_api_credentials()
    warehouse = warehouse_id or _resolve_warehouse_id()

    existing = [
        dashboard
        for dashboard in _list_dashboards(host, token)
        if dashboard.get("display_name") == DASHBOARD_DISPLAY_NAME
    ]
    for dashboard in existing:
        dashboard_id = dashboard.get("dashboard_id")
        if dashboard_id:
            print(f"[dashboard] Removing existing dashboard draft: {dashboard_id}")
            _delete_dashboard(dashboard_id, host, token)

    print(f"[dashboard] Creating Lakeview dashboard '{DASHBOARD_DISPLAY_NAME}'.")
    created = _api_request(
        "POST",
        "/api/2.0/lakeview/dashboards",
        host,
        token,
        {
            "display_name": DASHBOARD_DISPLAY_NAME,
            "warehouse_id": warehouse,
            "parent_path": DASHBOARD_PARENT_PATH,
            "serialized_dashboard": build_serialized_dashboard(),
        },
    )
    dashboard_id = created["dashboard_id"]

    print(f"[dashboard] Publishing dashboard {dashboard_id}.")
    _api_request(
        "POST",
        f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
        host,
        token,
        {"embed_credentials": True, "warehouse_id": warehouse},
    )

    dashboard_url = f"{host}/sql/dashboardsv3/{dashboard_id}"
    result = PublishedDashboard(
        dashboard_id=dashboard_id,
        display_name=DASHBOARD_DISPLAY_NAME,
        workspace_url=host,
        dashboard_url=dashboard_url,
        warehouse_id=warehouse,
    )
    print("[dashboard] Publish complete.")
    print(f"  Dashboard ID : {result.dashboard_id}")
    print(f"  Dashboard URL: {result.dashboard_url}")
    return result
