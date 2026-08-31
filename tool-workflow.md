# Tool Workflow — AI-Assisted Medallion Pipeline Development

Documentation of how **Cursor (Claude 3.5 Sonnet)** was used to design, implement, validate, and deploy the Databricks Medallion pipeline.

---

## 1. Primary AI Tool

| Attribute | Value |
|---|---|
| **Tool** | Cursor IDE |
| **Model** | Claude 3.5 Sonnet |
| **Role** | Pair-programming agent for architecture, code generation, debugging, and documentation |
| **Interaction modes** | Plan Mode, Composer (multi-file agent), Chat (targeted edits) |
| **Total prompts** | 30 (logged in `ai-prompts/`) |
| **Acceptance rate** | ~85–87% |
| **Rejection rate** | ~13–15% (architectural overrides required) |

---

## 2. Project Context Provisioning

### 2.1 Persistent Rules — `.cursorrules`

The workspace root `.cursorrules` file provides always-on constraints:

- Bronze lossless ingest with `_ingested_at`, `_source_file`
- Silver soft-quarantine (`dq_errors`, `quality_check_result`)
- LEFT OUTER JOIN for FK checks
- Gold PASS-only sourcing
- No Python UDFs
- Prompt logging to `ai-prompts/`

Cursor applies these rules to every agent interaction without re-stating them in each prompt.

### 2.2 Technical Specification — `tool-specific/cursor-workflow/spec.md`

Defines:

- CSV column schemas for all three entities
- The 460 spec-required intentional DQ defects
- Serves as the contract between data generation and silver validation

### 2.3 File Tagging (`@` References)

Context was injected per task by tagging relevant files:

| Task Type | Typical `@` Tags |
|---|---|
| Bronze ingest | `@spec.md`, `@.cursorrules`, `@src/bronze/` |
| Silver DQ | `@src/silver/`, `@ai-prompts/silver-layer.md` |
| Gold SQL | `@src/gold/`, `@data-model.md` |
| Debugging | `@database/debugging-notes.md`, `@tests/` |
| Documentation | `@candidate-info.md`, `@design-notes.md` |

### 2.4 Prompt Logs — `ai-prompts/`

Append-only logs by topic provide multi-session continuity:

- `bronze-layer.md`, `silver-layer.md`, `gold-layer.md`
- `dashboard.md`, `debugging.md`, `data-generation.md`
- `documentation.md`, `project_architecture.md`, `push_data_to_delta.md`

Each entry records: prompt sent, AI response summary, human evaluation (✓ / ✗ / △).

---

## 3. AI Usage Across the Lifecycle

### 3.1 Requirement Analysis

| Activity | AI Contribution | Human Role |
|---|---|---|
| Problem framing | Drafted functional/non-functional requirements from spec | Validated against assessment rubric |
| Edge case identification | Suggested null FK, duplicate, cancelled order scenarios | Confirmed soft-quarantine decision |
| Clarifications | Proposed hard-drop vs. quarantine trade-offs | Chose soft quarantine per architecture rules |

### 3.2 Pipeline Design

| Activity | AI Contribution | Human Role |
|---|---|---|
| Medallion layer design | Generated architecture diagrams and schema flow | Enforced LEFT JOIN and PASS-only gold |
| Module decomposition | Proposed five silver DQ modules + orchestrator | Approved modular `Column`-based API |
| Deployment pattern | Suggested notebook wrappers + job JSON configs | Tested on Databricks CE |

### 3.3 PySpark Code Generation

| Layer | AI Output | Human Review |
|---|---|---|
| Data generation | `generate_sample_data.py` with Faker/NumPy | Verified 700-defect manifest |
| Bronze | Ingest functions + `_metadata.file_path` fix | Rejected `input_file_name()` |
| Silver | Five DQ modules + `create_silver_tables.py` | Rejected INNER JOIN and `@udf` |
| Gold | Four SQL mart files | Validated PASS filter in every query |
| Dashboard | Three BI tile queries + guide | Confirmed visualization intent |

### 3.4 Validation & Testing

| Activity | AI Contribution | Human Role |
|---|---|---|
| Integration tests | `test_pipeline.py` with row parity and quarantine assertions | Set `MIN_QUARANTINED_ROWS = 400` |
| Unit tests | `test_silver_rules.py` per DQ helper | Ran on Databricks serverless |
| Test notebooks | `test_pipeline_nb.py`, `test_silver_rules_nb.py` | Submitted via `conf/test_*_run.json` |

### 3.5 Debugging

| Issue | AI Diagnosis | Human Fix |
|---|---|---|
| DBFS 403 | Suggested UC volume migration | Created `medallion_data` volume |
| All silver FAIL | Identified `array_remove` null bug | Switched to `array_filter` |
| ANSI cast error | Suggested `try_cast` | Applied in type validation module |
| Gold empty | Traced to silver all-FAIL | Re-ran pipeline after silver fix |

### 3.6 Data Quality

| Activity | AI Contribution | Human Role |
|---|---|---|
| DQ rule design | Generated modular `check_*` functions | Enforced vectorized-only pattern |
| FK validation | Initially proposed INNER JOIN | **Rejected** — mandated LEFT OUTER JOIN |
| Metrics reporting | `DqMetricsSummary` + `print_dq_metrics_summary()` | Verified output format |

---

## 4. Interaction Mode Selection

| Mode | When Used | Example |
|---|---|---|
| **Plan Mode** | Task decomposition before implementation | Breaking silver layer into 5 modules + orchestrator |
| **Composer** | Multi-file scaffolding | Bronze ingest suite (4 modules + notebooks + conf JSON) |
| **Chat** | Targeted refactoring | Fix `array_filter` bug in `create_silver_tables.py` |
| **Chat + `@` tags** | Context-heavy edits | `@spec.md` data generation with defect manifest |

---

## 5. Responsible AI & Data Governance

### 5.1 No Real PII

- All customer names, emails, and addresses generated by **Faker** with fixed seed.
- No production data uploaded to Databricks or shared in prompts.
- Assessment uses synthetic CSVs only.

### 5.2 Credential Hygiene

- Databricks tokens stored in `~/.databrickscfg` (never committed).
- `conf/databrickscfg.example` provides template without secrets.
- AI prompts referenced profile name (`community`) not token values.

### 5.3 Prompt Logging Transparency

- Every substantive prompt logged to `ai-prompts/` for auditability.
- Human evaluation marks (✓ / ✗ / △) document acceptance decisions.
- `database/final-ai-usage-summary.md` aggregates metrics.

### 5.4 Architectural Guardrails

`.cursorrules` prevents AI from:

- Silently dropping bad rows (INNER JOIN trap)
- Introducing performance anti-patterns (UDFs)
- Skipping audit metadata in bronze

---

## 6. Reusable Production Patterns

### 6.1 What Worked

| Pattern | Benefit |
|---|---|
| `.cursorrules` + `spec.md` dual context | Consistent architecture across 30 prompts |
| Modular `Column`-returning DQ functions | Composable, testable, Catalyst-friendly |
| `array_filter` for error aggregation | Reliable null handling on Databricks |
| LEFT JOIN + alias for FK checks | Orphan rows preserved for quarantine |
| Notebook + job JSON deployment | Repeatable CE execution |
| Integration tests on Databricks | Catches runtime-specific bugs (UC metadata, ANSI) |
| Fixed random seed | Reproducible defect injection |

### 6.2 What Failed (Lessons Learned)

| Failure | Root Cause | Corrective Action |
|---|---|---|
| INNER JOIN for FK validation | AI default join semantics | Codified LEFT OUTER JOIN in `.cursorrules` |
| `@udf` for DQ checks | AI Python-first instinct | Banned UDFs in `.cursorrules` |
| `input_file_name()` on UC | CE/UC API difference | Use `_metadata.file_path` |
| `array_remove(..., None)` | Databricks null sentinel bug | Use `array_filter` with lambda |
| DBFS FileStore paths | CE permission restrictions | Migrate to UC volumes |
| Assuming 100K orders | Spec vs. implementation drift | Document actual `NUM_ORDERS = 50_000` in tests |

### 6.3 Recommended Workflow for Future Projects

1. **Write `.cursorrules` first** — encode non-negotiable architecture before any code generation.
2. **Maintain `spec.md`** — single source of truth for schemas and defect counts.
3. **Use Plan Mode** for layer decomposition, Composer for scaffolding, Chat for fixes.
4. **Log every prompt** — enables acceptance rate tracking and knowledge transfer.
5. **Test on target runtime early** — local Spark ≠ Databricks CE behavior.
6. **Reject aggressively** — 15% rejection rate prevented production-critical bugs.

---

## 7. Metrics Summary

| Metric | Value |
|---|---|
| Total prompts | 30 |
| Files generated/modified | 90+ |
| Databricks job runs | 20+ |
| Intentional DQ defects | 700 |
| Integration test quarantine threshold | > 400 FAIL rows |
| Estimated time savings | 60–70% vs. manual implementation |

See `database/final-ai-usage-summary.md` for detailed prompt distribution and time-savings breakdown.
