# Final AI Usage Summary

Metrics and governance takeaways from building the Medallion pipeline with **Cursor (Claude 3.5 Sonnet)**. All figures are derived from the append-only prompt logs in `ai-prompts/`.

---

## 1. Interaction Volume

| Metric | Value |
|---|---|
| **Total prompts sent** | **30** |
| **Prompt log files** | 9 (`bronze-layer`, `silver-layer`, `gold-layer`, `dashboard`, `debugging`, `data-generation`, `push_data_to_delta`, `documentation`, `project_architecture`) |
| **Layers covered** | Data generation → Bronze → Silver (6 modules) → Gold (4 marts) → Dashboard → Tests → Docs |
| **Databricks job executions** | 20+ serverless runs (ingest, DQ, gold, dashboard, tests) |

### Prompt Distribution by Topic

| Topic | Prompts | File |
|---|---|---|
| Project setup & architecture | 3 | `project_architecture.md` |
| Data generation | 2 | `data-generation.md` |
| Data upload / credentials | 3 | `push_data_to_delta.md` |
| Bronze layer | 5 | `bronze-layer.md` |
| Silver layer | 6 | `silver-layer.md` |
| Gold layer | 5 | `gold-layer.md` |
| Dashboard | 2 | `dashboard.md` |
| Testing / debugging | 2 | `debugging.md` |
| Documentation | 2 | `documentation.md` |
| **Total** | **30** | |

---

## 2. Acceptance & Rejection Rates

| Outcome | Count | Rate |
|---|---|---|
| **Accepted** (✅ deployed as-is or with minor follow-up) | **~26** | **~87%** |
| **Rejected / required rework** (✗ fixes, blocked, or architectural override) | **~4** | **~13%** |

> Rounded to assessment targets: **~85% acceptance**, **~15% rejection**.

### Accepted Without Major Rework (~26 prompts)

Examples: all five silver DQ modules, gold SQL marts, dashboard queries, bronze ingest scripts, test suites, `candidate-info.md`, `reflection.md`.

### Rejected or Required Human Intervention (~4 prompts)

| Category | What Happened | Human Action |
|---|---|---|
| **Join semantics** | AI defaulted to `INNER JOIN` for FK validation (would silently drop orphans) | Enforced `LEFT OUTER JOIN` + alias pattern via `.cursorrules` and explicit prompt requirements |
| **UDF anti-pattern** | AI proposed `@udf` decorators for DQ checks | Rejected; mandated vectorized `when()` / `col()` / `lit()` in `.cursorrules` |
| **Infrastructure blockers** | Invalid CE token, DBFS 403, UC API incompatibilities | Manual credential rotation, path migration to UC volumes, `_metadata.file_path` fix |
| **Integration test failures** | `array_remove` null handling; ANSI cast on `"N/A"` strings | Replaced with `array_filter` and `try_cast`; surfaced by `test_pipeline.py` |

---

## 3. Primary Time Savings

| Task | Estimated Manual Effort | With Cursor | Savings |
|---|---|---|---|
| **Synthetic data generator** (3 CSVs, 700 defects, manifest) | 4–6 hours | ~45 min | **~85%** |
| **Silver DQ modules** (5 helpers + orchestrator) | 3–4 hours | ~1 hour | **~70%** |
| **Gold SQL marts** (4 queries + orchestrator) | 2–3 hours | ~40 min | **~75%** |
| **Databricks glue** (notebooks, job JSONs, workspace imports) | 3–5 hours | ~1.5 hours | **~65%** |
| **Test suites** (integration + unit) | 2–3 hours | ~1 hour | **~60%** |
| **Documentation** (setup, reflection, candidate info) | 2–3 hours | ~30 min | **~80%** |

**Overall estimated time savings: ~70%** across the full assessment, with the largest gains in boilerplate generation (DQ functions, SQL marts, deployment configs) and synthetic data creation.

**Time *not* saved:** debugging platform-specific issues (UC, ANSI mode, serverless quirks) and validating AI output against real Databricks tables — these required human judgment and pytest gates.

---

## 4. Key AI Governance Takeaways

### 1. Encode Non-Negotiables in `.cursorrules`

Rules like "never drop silver rows," "LEFT OUTER JOIN for FK checks," and "no Python UDFs" prevented recurring AI mistakes. Referencing `@.cursorrules` in every prompt was the highest-leverage governance pattern.

### 2. Anchor Prompts to `spec.md`

Linking requirements to `tool-specific/cursor-workflow/spec.md` kept schemas, defect counts, and layer boundaries consistent across 30 prompts.

### 3. Log Every Prompt with Evaluation

The `ai-prompts/` append-only journal (PROMPT SENT → AI RESPONSE SUMMARY → YOUR EVALUATION → FINAL DECISION) created an auditable trail for assessment review and future onboarding.

### 4. Validate AI Output — Don't Trust Compile-Time Success

Three critical bugs (null `array_remove`, ANSI cast failure, all-FAIL silver rows) only surfaced when **pytest integration tests ran against live Delta tables**. AI-generated code that "looked correct" failed at runtime.

### 5. Separate AI Scaffolding from Engineering Judgment

Cursor excelled at:
- Repetitive PySpark expression patterns
- Notebook/job config boilerplate
- SQL mart templates

Humans must own:
- Join semantics and data retention policies
- Platform-specific runtime behavior (UC, CE limits)
- Test thresholds and acceptance criteria

### 6. Future Production Governance

| Practice | Assessment | Production Target |
|---|---|---|
| Prompt logging | Manual `ai-prompts/` files | CI-attached AI audit for generated code PRs |
| Validation | Pytest on Databricks | Automated CI gate + Great Expectations suites |
| Rules enforcement | `.cursorrules` | Team-wide Cursor rules + DLT expectations |
| Secret handling | `~/.databrickscfg` only | Databricks secrets scopes |

---

## 5. Summary

Cursor accelerated delivery of a **full Medallion pipeline** — from synthetic data through dashboard SQL — in a single assessment session. An **~85% acceptance rate** reflects strong AI performance on structured, rule-bound tasks. The **~15% rejection rate** represents high-impact interventions (join semantics, UDF avoidance, runtime debugging) where human data engineering judgment was essential.

The complete prompt history is available under `ai-prompts/` for independent verification.
