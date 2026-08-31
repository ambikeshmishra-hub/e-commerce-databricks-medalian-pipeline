# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Rules — Unit Tests
# MAGIC Runs isolated unit tests for silver DQ helper functions (`01`–`05`).

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Shared/medallion-pipeline")

from tests.test_silver_rules import run_silver_rules_tests

# COMMAND ----------

run_silver_rules_tests(spark)
