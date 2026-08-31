# AI Prompts — Documentation

## Prompt 1: Candidate Info Document

**PROMPT SENT:**
"@spec.md @.cursorrules
Structure: Create `candidate-info.md`.
Purpose: Provide complete candidate, environment, and execution metadata as mandated by the evaluation template.

Requirements:
1. Candidate Metadata:
   - Name: Ambikesh Mishra
   - Role: Senior Data Engineer / Technical Lead[cite: 1]
   - Primary Stack: Python / PySpark, Delta Lake, SQL, Databricks[cite: 1]
   - Primary AI Tool: Cursor (Claude 3.5 Sonnet engine)[cite: 1]
   - Project Option: Data Pipeline (Medallion Architecture)[cite: 1]
   - Dates: Assessment Start Date and Submission Date[cite: 1]
2. Tools & Runtime Environment:
   - Databricks Community Edition / Single Node Cloud Cluster[cite: 1]
   - Databricks Runtime 13.3+ LTS (Apache Spark 3.4.1, Scala 2.12)
   - Libraries: PySpark, Delta Lake, pandas, numpy, faker, pytest[cite: 1]
3. Quickstart Pipeline Run Sequence:
   - Exact CLI commands to generate synthetic data, run Bronze, Silver, and Gold pipelines, and trigger pytest validation tests[cite: 1]."

**AI RESPONSE SUMMARY:**
Created `candidate-info.md` with candidate metadata table, Databricks CE runtime/library details, step-by-step quickstart CLI commands (data generation, volume upload, bronze/silver/gold job submits, pytest local + Databricks), workspace paths, and validation summary.

**YOUR EVALUATION:**
✓ **What was good:**
- Matches evaluation template structure
- Commands align with actual `conf/*.json` job configs and UC volume paths
- Documents both local pytest and Databricks serverless test execution

**FINAL DECISION:**
✅ **Accepted** — candidate submission metadata document complete.

---

## Prompt 2: Technical Reflection Document

**PROMPT SENT:**
"@spec.md @.cursorrules @src/ @ai-prompts/
Structure: Create `reflection.md`.
Purpose: Provide an in-depth, candid technical reflection on building the Medallion pipeline with Cursor[cite: 1].

Requirements:
1. What I Built:
   - End-to-end Medallion Architecture (Bronze lossless ingestion -> Silver soft-quarantine DQ -> Gold aggregations -> BI visual queries)[cite: 1].
2. How I Used AI Across the Lifecycle:
   - Plan mode for task decomposition, Composer for multi-file scaffolding, and Chat for targeted refactoring and prompt logs[cite: 1].
3. What AI Helped With Most:
   - Rapid generation of synthetic data with anomalies using Faker[cite: 1].
   - Boilerplate reduction for PySpark schemas and modular DQ functions[cite: 1].
4. What AI Got Wrong & Human Interventions:
   - Detail the foreign key validation issue: Cursor initially generated an `INNER JOIN` that silently filtered out invalid keys[cite: 1]. Document how I rejected it and enforced `LEFT OUTER JOIN`s to preserve orphan rows for quarantine[cite: 1].
   - Detail the PySpark UDF anti-pattern: Cursor attempted Python `@udf` decorators; I forced vectorized native Spark functions via `.cursorrules`.
5. How I Validated AI Output:
   - Pytest test suite asserting soft-quarantine error counts (>400 caught) and Gold table data purity[cite: 1].
6. Reusable Patterns & Future Improvements:
   - Establishing `.cursorrules` + `spec.md` for AI context management[cite: 1].
   - Scaling with Delta Live Tables (DLT) and Great Expectations in production."

**AI RESPONSE SUMMARY:**
Created `reflection.md` with six sections covering the full pipeline deliverable, Cursor usage across plan/composer/chat modes, AI strengths (Faker data gen, DQ boilerplate), human interventions (LEFT OUTER JOIN vs INNER JOIN, UDF rejection, array_filter/try_cast fixes), pytest validation strategy, and future improvements (DLT, Great Expectations).

**YOUR EVALUATION:**
✓ **What was good:**
- Candid about AI failures, not just successes
- Grounded in actual project artifacts (`ai-prompts/`, `.cursorrules`, test assertions)
- Links engineering decisions to reproducible validation

**FINAL DECISION:**
✅ **Accepted** — technical reflection document complete.

---

## Prompt 3: Database Documentation Suite

**PROMPT SENT:**
"@spec.md @src/
Structure: Create `database/setup-notes.md`, `database/debugging-notes.md`, and `database/final-ai-usage-summary.md`.
Purpose: Document environment setup, troubleshooting logs, and final AI interaction metrics[cite: 1].

Requirements:
1. `database/setup-notes.md`:
   - Detailed guide on configuring Databricks workspace/cluster, importing repository files, creating tables via `database/schema.sql`, and setting paths[cite: 1].
2. `database/debugging-notes.md`:
   - Document 3 real debugging scenarios encountered:
     * Issue 1: Column name ambiguity (`AnalysisException: Reference 'customer_id' is ambiguous`) during parent-child joins in Silver. Fix: renamed parent keys prior to join[cite: 1].
     * Issue 2: Future signup dates in synthetic customer generation. Fix: clamped date ranges to current date[cite: 1].
     * Issue 3: Schema evolution mismatch when writing Delta tables. Fix: used `option("overwriteSchema", "true")`.
3. `database/final-ai-usage-summary.md`:
   - Summary metrics: total prompts sent, acceptance rate (~85%), rejection rate (~15%), primary time savings, and key AI governance takeaways[cite: 1]."

**AI RESPONSE SUMMARY:**
Created `database/setup-notes.md` (CE workspace, CLI, schema bootstrap, UC volume paths, workspace imports, pipeline order), `database/debugging-notes.md` (three documented issues + additional integration-test findings), `database/final-ai-usage-summary.md` (30 prompts, ~87%/~13% accept/reject, ~70% time savings, governance takeaways), and `database/schema.sql` for UC schema bootstrap.

**YOUR EVALUATION:**
✓ **What was good:**
- Grounded in actual project paths, fixes, and ai-prompts audit trail
- Debugging notes tie to real code changes in silver/bronze modules
- Metrics derived from logged prompt files

**FINAL DECISION:**
✅ **Accepted** — database documentation suite complete.

---

## Prompt 4: Technical Reflection (database path sync)

**PROMPT SENT:**
"@spec.md @.cursorrules @src/ @ai-prompts/
Structure: Create `reflection.md`.
Purpose: Provide an in-depth, candid technical reflection on building the Medallion pipeline with Cursor[cite: 1].
[Requirements 1–6 as specified]"

**AI RESPONSE SUMMARY:**
Synced full reflection content to `database/reflection.md` (canonical per project architecture). Root `reflection.md` now points to the database copy. Content covers all six sections: pipeline deliverable, AI lifecycle, strengths, human interventions (LEFT JOIN, UDF rejection), pytest validation, and future improvements (DLT, Great Expectations).

**YOUR EVALUATION:**
✓ **What was good:**
- Complete six-section reflection already authored; synced to correct project path
- Candid coverage of AI failures and validation strategy

**FINAL DECISION:**
✅ **Accepted** — reflection available at `database/reflection.md`.

---

## Prompt 5: Populate All Blank Documentation Files

**PROMPT SENT:**
"@spec.md @.cursorrules
Act as a Principal Data Engineer. The following files in our workspace are currently blank. Populate every single one of these files with complete, exhaustive, professional content aligned strictly with our Databricks Medallion Architecture requirements and the participant guide:

1. `requirements-analysis.md`:
   - Problem statement in your own words (e-commerce sales ingestion from multi-source CSVs to Databricks)[cite: 1].
   - Functional requirements for all layers (Data Gen, Bronze, Silver, Gold, Dashboard)[cite: 1].
   - Non-functional requirements (Scalability, performance, Catalyst optimization, idempotency, zero data loss)[cite: 1].
   - Assumptions (USD currency, transaction lifecycle)[cite: 1].
   - Edge cases (null foreign keys, duplicates, cancelled orders)[cite: 1].
   - Clarifications addressed (soft quarantine vs hard drops)[cite: 1].

2. `design-notes.md`:
   - High-level architecture overview (Bronze -> Silver -> Gold -> Dashboard)[cite: 1].
   - Data models & schema flow across layers[cite: 1].
   - Bronze design (lossless ingestion, `_ingested_at`, `_source_file` metadata)[cite: 1].
   - Silver design (soft quarantine, `dq_errors` array column, `quality_check_result` ['PASS'/'FAIL'])[cite: 1].
   - Gold design (business aggregations sourcing strictly clean records)[cite: 1].
   - Data quality validation strategy & debugging approach (pre-join renaming, eliminating UDFs)[cite: 1].

3. `data-model.md`:
   - Full schema definitions for all layers:
     * Bronze: `bronze_customers`, `bronze_orders`, `bronze_products` (with metadata columns)[cite: 1].
     * Silver: `silver_orders` (including `dq_errors` ARRAY<STRING> and `quality_check_result` STRING)[cite: 1].
     * Gold: `gold_sales_by_product`, `gold_revenue_by_customer`, `gold_daily_weekly_trends`, `gold_customer_segmentation`[cite: 1].
   - Primary keys, foreign keys, data types, nullability, and descriptions for every field[cite: 1].

4. `data-quality-strategy.md`:
   - Exhaustive breakdown of all quality check categories: Completeness, Uniqueness, Referential Integrity, Type Validation, and Business Logic[cite: 1].
   - Threshold metrics (>99% completeness, 100% uniqueness, >99.9% FK validity)[cite: 1].
   - Metrics reporting format (% passed/failed summary output)[cite: 1].
   - Explicit mapping of the ~700 intentional sample data defects (50 null emails, 10 dup customers, 100 null cust_ids, 200 null prod_ids, 50 orphan cust_ids, 30 orphan prod_ids, 20 dup order_ids)[cite: 1].

5. `tool-workflow.md`:
   - Primary AI tool used (Cursor with Claude 3.5 Sonnet engine)[cite: 1].
   - How project context was provided (`.cursorrules`, `@spec.md`, file tags)[cite: 1].
   - How AI was used across requirement analysis, pipeline design, PySpark code generation, validation, testing, debugging, and data quality[cite: 1].
   - Responsible AI & data governance: Avoiding PII sharing, generating synthetic seed data with Faker[cite: 1].
   - Reusable production patterns and lessons learned (what worked, what failed like inner join drops)[cite: 1].

6. `database/seed-data-notes.md`:
   - Descriptions of the 3 seed datasets: `customers.csv` (10k rows, ~500 KB), `orders.csv` (100k rows, ~2-3 MB), and `products.csv` (500 rows, ~50 KB)[cite: 1].
   - Statistical distribution of values (customer segments, order statuses, price ranges)[cite: 1].
   - How the seed data simulates production volume and intentional anomalies[cite: 1].

7. `tool-specific/cursor-workflow/project-context.md`:
   - Setup of persistent workspace context for Cursor[cite: 1].
   - Multi-session context maintenance strategy using `@` file referencing[cite: 1].
   - How Cursor Plan Mode and Composer Agent were used to enforce architecture boundaries[cite: 1].

8. `tool-specific/cursor-workflow/cursor-rules-or-instructions.md`:
   - Comprehensive documentation of all workspace rules, instructions, and standard practices[cite: 1].
   - PySpark standards (no `@udf` decorators, vectorized operations only, window-based deduplication, left outer join referential integrity, quarantine flagging)[cite: 1].

9. `tool-specific/cursor-workflow/task-breakdown.md`:
   - Granular, checklist-style task decomposition as defined to Cursor across Data Generation, Bronze Ingestion, Silver Quality Checks, Gold Aggregations, Dashboard Queries, and Unit/Integration Testing[cite: 1].

10. `src/__init__.py`:
    - Proper Python package initialization docstring.

11. `src/data_generation/DATA_GENERATION_NOTES.md`:
    - Technical notes on `generate_sample_data.py`: libraries used (Pandas, NumPy, Faker), random seed setting for reproducibility, and exact line-by-line breakdown of how the ~700 flawed rows were injected[cite: 1].

Generate complete, production-ready Markdown and Python files without any placeholders or truncation[cite: 1]."

**AI RESPONSE SUMMARY:**
Populated all 11 previously blank files with production-ready content grounded in actual implementation (`generate_sample_data.py`, silver DQ modules, gold SQL, tests). Documents actual volumes (50K orders, 1K products, 10K+ customers) while noting participant guide targets. Covers LEFT JOIN override, UDF rejection, array_filter fix, 700-defect manifest, and DLT/GE future improvements.

**YOUR EVALUATION:**
✓ good

**FINAL DECISION:**
✅ **Accepted** — documentation suite complete.
