# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard — Publish Lakeview Dashboard
# MAGIC Validates gold tile queries and publishes **E-Commerce Gold Analytics** via Lakeview API.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.dashboard.publish_dashboard import publish_gold_dashboard

# COMMAND ----------

published = publish_gold_dashboard(spark, validate_queries=True)
print(f"\nPublished dashboard: {published.dashboard_url}")
