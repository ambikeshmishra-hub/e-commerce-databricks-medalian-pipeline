# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard — Setup Guide Validation
# MAGIC Validates all three BI tile queries referenced in `DASHBOARD_GUIDE.md`.

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from src.dashboard.run_dashboard_queries import run_dashboard_queries

GUIDE_PATH = "/Workspace/Shared/medallion-pipeline/src/dashboard/DASHBOARD_GUIDE.md"

# COMMAND ----------

print("Dashboard guide location:")
print(GUIDE_PATH)
print("\n--- DASHBOARD_GUIDE.md (preview) ---\n")

with open(GUIDE_PATH, encoding="utf-8") as guide_file:
  guide_lines = guide_file.readlines()

for line in guide_lines[:25]:
  print(line.rstrip())

print("\n... (open the full guide in the workspace path above) ...\n")

# COMMAND ----------

run_dashboard_queries(spark)

print("\n[dashboard] Guide validation complete — all tile queries executed successfully.")
print("[dashboard] Follow DASHBOARD_GUIDE.md to configure the SQL Dashboard UI.")
