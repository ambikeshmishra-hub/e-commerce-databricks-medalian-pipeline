# Technical Reflection — Building a Medallion Pipeline with Cursor

A candid account of designing, implementing, and validating an end-to-end Databricks Medallion pipeline using Cursor as the primary AI development tool.

---

## 1. What I Built

I delivered a complete **e-commerce Medallion pipeline** on Databricks Community Edition, spanning raw ingestion through analytics-ready gold marts and dashboard SQL.

### Bronze — Lossless Ingestion

- **Modules:** `src/bronze/01_ingest_customers.py`, `02_ingest_orders.py`, `03_ingest_products.py`, orchestrated by `ingest_all.py`
- **Behavior:** Reads CSVs from a Unity Catalog volume (`workspace.default.medallion_data`), appends audit metadata (`_ingested_at`, `_source_file`), and overwrites Delta tables in `workspace.bronze`
- **Design principle:** No transformations, no row drops — bronze mirrors source files exactly

### Silver — Soft-Quarantine Data Quality

- **Modular DQ helpers** (`src/silver/01`–`05`):
  - Completeness, uniqueness, type validation, referential integrity, business logic
- **Orchestrator:** `create_silver_tables.py` applies all checks to `bronze_orders`, producing `workspace.silver.silver_orders` with:
  - `dq_errors` — `ARRAY<STRING>` of error tags per row
  - `quality_check_result` — `PASS` or `FAIL`
- **Design principle:** Flag bad rows; never silently discard them

### Gold — PASS-Only Analytical Marts

- **SQL marts** (`src/gold/01`–`04`):
  - Sales by product, revenue by customer, daily/weekly trends, customer segmentation
- **Orchestrator:** `create_gold_tables.py` executes all four `.sql` files sequentially
- **Design principle:** Gold reads only `quality_check_result = 'PASS'` rows

### Dashboard & Validation

- **BI queries:** `src/dashboard/dashboard_queries.sql` — three production-ready tiles (bar, histogram, pie/donut)
- **Setup guide:** `src/dashboard/DASHBOARD_GUIDE.md`
- **Tests:** `tests/test_pipeline.py` (integration), `tests/test_silver_rules.py` (unit)

### Synthetic Data Foundation

- `src/data_generation/generate_sample_data.py` produces ~50,000 orders, 10,000 customers, and 1,000 products with **~700 intentional DQ defects** mapped to a documented `ISSUE_MANIFEST`

---

## 2. How I Used AI Across the Lifecycle

Cursor was embedded at every stage — not as a one-shot code generator, but as a **structured co-pilot** governed by project rules and logged prompts.

| Phase | Cursor Mode / Feature | How I Used It |
|---|---|---|
| **Planning** | Plan mode | Decomposed the assessment into layer-by-layer tasks (bronze → silver modules → silver orchestrator → gold SQL → dashboard → tests → docs) before writing code |
| **Scaffolding** | Composer (multi-file) | Generated folder structures, paired `.py` modules with `_nb.py` Databricks notebooks, and `conf/*_run.json` job configs in single sessions |
| **Implementation** | Chat + `@` context | Targeted prompts with `@spec.md`, `@.cursorrules`, and `@src/silver/` to keep outputs aligned with architecture rules |
| **Refactoring** | Chat | Fixed Databricks-specific issues (Unity Catalog `input_file_name()` → `_metadata.file_path`, `array_remove` → `array_filter`, ANSI `try_cast`) |
| **Audit trail** | Prompt logging | Every user prompt recorded verbatim in `ai-prompts/*.md` with evaluation notes — creating a reproducible AI decision history |

The `ai-prompts/` directory became an **append-only engineering journal**: what was asked, what the AI produced, what was accepted, and what needed human correction.

---

## 3. What AI Helped With Most

### Rapid Synthetic Data with Realistic Anomalies

Cursor generated `generate_sample_data.py` quickly using **Faker** for realistic names/emails, **NumPy** for distributions, and a manifest-driven defect injector. The AI correctly mapped spec requirements (NULL FKs, duplicate IDs, invalid segments) into reproducible, seed-controlled CSV output — work that would have taken hours of manual scripting.

### Boilerplate Reduction for PySpark DQ Functions

The five silver helper modules follow a consistent pattern:

```python
def check_<rule>(...) -> Column:
    return when(<condition>, lit(error_tag))
```

Cursor excelled at producing this **expression-only, composable API** — each function returns a `Column` suitable for building `dq_errors` arrays without UDFs or row-level Python callbacks. Type hints, docstrings, and `src/silver/__init__.py` re-exports were generated consistently across modules.

### Databricks Deployment Glue

Notebook wrappers, workspace import commands, and serverless `jobs submit` JSON configs were generated reliably once the pattern was established — reducing repetitive DevOps scaffolding across 15+ deployable artifacts.

---

## 4. What AI Got Wrong & Human Interventions

### Foreign Key Validation: INNER JOIN vs. LEFT OUTER JOIN

**The problem:** When designing referential integrity checks, AI models naturally gravitate toward `INNER JOIN` between child and parent tables — it "feels" correct because you only want rows with valid parents. In a Medallion **soft-quarantine** design, this is a critical mistake: `INNER JOIN` silently **drops orphan records**, defeating the entire purpose of flagging bad data instead of deleting it.

**My intervention:**

1. Codified the rule in `.cursorrules`: *"Silver Joins: Always use LEFT OUTER JOINs for referential integrity checks to preserve orphan records."*
2. Explicitly required `LEFT OUTER JOIN` in the `04_quality_referential_integrity.py` prompt
3. Implemented a two-step pattern the AI could not shortcut:
   - `check_foreign_key()` — LEFT JOIN child to distinct parent keys, adding `matched_*` alias column
   - `flag_invalid_fk()` — tag rows where `fk_col IS NOT NULL AND alias_col IS NULL`

This preserves every orphan row for quarantine while still detecting invalid foreign keys. The integration test `test_silver_soft_quarantine_anomaly_detection` enforces `silver_orders.count() == bronze_orders.count()` — a guardrail that would immediately catch any regression to INNER JOIN behavior.

### PySpark UDF Anti-Pattern

**The problem:** Cursor occasionally proposed `@udf`-decorated Python functions for DQ checks (e.g., custom email validation, segment assignment). Python UDFs serialize rows across the JVM-Python boundary, **killing Spark performance** and breaking Catalyst optimizer pushdown.

**My intervention:**

- Added to `.cursorrules`: *"NEVER use Python UDFs (`@udf`). Use native vectorized PySpark functions."*
- Rejected any generated UDF code and redirected to `when()`, `col()`, `lit()`, `count().over(Window...)`, and `try_cast()` expressions
- Updated `check_numeric_positive` to use `try_cast(... AS DOUBLE)` after integration tests revealed ANSI mode cast failures on string values like `"N/A"`

### Additional Corrections (Discovered During Validation)

| Issue | AI Output | Human Fix |
|---|---|---|
| `array_remove(array(...), None)` | Seemed correct per docs | All 50,000 rows marked `FAIL` on Databricks — replaced with `array_filter(..., lambda x: x.isNotNull())` |
| `input_file_name()` on UC volumes | Standard bronze pattern | Not supported on Unity Catalog — switched to `_metadata.file_path` |
| DBFS `FileStore` upload | Default path | Community Edition blocks public DBFS root — migrated to UC volume |
| Duplicate ID injection | Overwrite rows in-place | Changed to append duplicate rows to avoid orphan FK side effects |

These were not caught by code review alone — they surfaced when **pytest integration tests ran against live Databricks tables**.

---

## 5. How I Validated AI Output

Validation was layered: unit tests for isolated logic, integration tests for pipeline integrity, and manual Databricks job execution for deployment confidence.

### Pytest Integration Suite (`tests/test_pipeline.py`)

| Test | Assertion | What It Proves |
|---|---|---|
| `test_bronze_ingestion_counts` | Row volumes + non-null `_ingested_at` / `_source_file` | Bronze ingest is lossless and auditable |
| `test_silver_soft_quarantine_anomaly_detection` | `silver.count() == bronze.count()`; `FAIL > 400`; PASS rows have empty `dq_errors` | Soft-quarantine catches anomalies without dropping rows |
| `test_gold_layer_integrity` | Gold tables non-empty; revenue > 0; valid behavioral segments | Gold marts are populated and financially sane |

The **`FAIL > 400`** threshold directly validates that the ~700 intentional defects in generated data are being detected (not all 700 become unique FAIL rows due to overlapping error tags, but 400+ is a strong signal).

### Pytest Unit Suite (`tests/test_silver_rules.py`)

Isolated tests with small in-memory DataFrames verify each DQ helper independently — catching logic bugs without requiring full pipeline materialization.

### Databricks Serverless Execution

Every layer was deployed and executed via `databricks jobs submit` with captured run URLs logged in `ai-prompts/`. This confirmed that code working locally also works on Community Edition serverless compute with Unity Catalog.

### Prompt Log Review

The `ai-prompts/` files served as a manual audit: for each AI-generated artifact, I recorded ✓ good / ✗ fixes / △ missing evaluations before accepting code into the pipeline.

---

## 6. Reusable Patterns & Future Improvements

### Patterns I Would Reuse

**`.cursorrules` + `spec.md` as AI context anchors**

Referencing `@.cursorrules` and `@spec.md` in every prompt kept the AI aligned on non-negotiable architecture decisions (soft-quarantine, LEFT JOIN, no UDFs, PASS-only gold). This is the single highest-leverage pattern for AI-assisted data engineering — **encode your engineering standards once, enforce them in every prompt**.

**Modular DQ expression library**

The `01`–`05` silver modules returning `Column` expressions composable into `dq_errors` arrays is reusable across any entity (customers, products, orders). Adding a new check means one function + one line in the array — no pipeline rewrite.

**Paired module + notebook + job config**

Every deployable unit follows `src/<layer>/<module>.py` + `<module>_nb.py` + `conf/<module>_run.json`. Cursor learned this pattern quickly and applied it consistently.

**Prompt logging as an AI audit trail**

`ai-prompts/*.md` provides evaluators (and future me) a transparent record of what AI generated vs. what I accepted or rejected.

### Future Improvements

| Area | Current State | Production Target |
|---|---|---|
| **Orchestration** | Sequential `jobs submit` via CLI | **Delta Live Tables (DLT)** pipelines with declarative expectations, automatic lineage, and built-in data quality monitoring |
| **Data quality framework** | Custom `when()` expressions | **Great Expectations** or **Databricks DQ** for standardized expectation suites, profiling, and data docs |
| **CI/CD** | Manual workspace imports | Git-backed Databricks Repos with automated test gates on PR |
| **Data volume** | 50K orders (CE limits) | Scale generator to 100K+ rows; partition bronze/silver by `order_date` |
| **Monitoring** | Print-based DQ metrics summary | Push quarantine rates to Datadog / Databricks SQL alerts |
| **Gold layer** | Static SQL marts | Incremental gold refreshes with merge keys; SCD Type 2 for customer dimension |

---

## Closing Thought

Cursor accelerated scaffolding and boilerplate dramatically, but **the Medallion architecture's correctness depended on human judgment** — especially around join semantics, UDF avoidance, and validation-driven debugging. The `.cursorrules` file and pytest suite were not optional extras; they were the mechanisms that turned AI-generated code into a trustworthy pipeline.

The full prompt history, run URLs, and per-layer evaluations are available under `ai-prompts/` for independent review.
