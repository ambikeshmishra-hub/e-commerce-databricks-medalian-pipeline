# Project Context — Cursor Workspace Configuration

How persistent AI context was established and maintained across multiple Cursor sessions for the Databricks Medallion pipeline project.

---

## 1. Persistent Workspace Context

### 1.1 Context Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: .cursorrules (always applied)                     │
│  Architecture rules, coding standards, prompt logging       │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: tool-specific/cursor-workflow/spec.md             │
│  CSV schemas, defect manifest, technical contract           │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: ai-prompts/*.md (session history)                 │
│  Prior prompts, decisions, evaluations per topic            │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: @ file tags (per-interaction)                     │
│  Source code, configs, docs relevant to current task          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Repository as Context Store

The repository itself serves as the AI's long-term memory:

| Directory | Context Purpose |
|---|---|
| `src/` | Implementation truth—bronze, silver, gold, dashboard, tests |
| `conf/` | Databricks job execution contracts |
| `database/` | Setup notes, debugging history, schema bootstrap |
| `ai-prompts/` | Decision audit trail with human evaluations |
| `data/` | Generated CSV artifacts |
| `tool-specific/cursor-workflow/` | Workflow specs and task decomposition |

---

## 2. `.cursorrules` Setup

The workspace rules file at the repository root encodes **non-negotiable architecture constraints**:

1. Bronze lossless ingest with metadata columns
2. Silver soft-quarantine (never drop bad rows)
3. LEFT OUTER JOIN for referential integrity
4. Gold PASS-only sourcing
5. No Python UDFs
6. Prompt logging protocol

**Why this matters:** Without `.cursorrules`, the AI defaults to common patterns (INNER JOIN for FK validation, `@udf` for custom logic) that violate Medallion DQ requirements. The rules file acts as a persistent system prompt that applies to Plan Mode, Composer, and Chat.

---

## 3. `spec.md` as Technical Contract

`tool-specific/cursor-workflow/spec.md` defines:

- Exact CSV column names and types
- The 460 spec-required intentional defects
- Serves as the bridge between data generation and silver validation

**Usage pattern:**

```
@spec.md @.cursorrules
Generate the data generation script with exactly 700 defects...
```

---

## 4. Multi-Session Context Maintenance

### 4.1 The `@` File Referencing Strategy

Cursor's `@` tag system injects file contents into the prompt context window. Strategy by task:

| Session Goal | `@` Tags |
|---|---|
| New layer implementation | `@spec.md`, `@.cursorrules`, `@src/<layer>/` |
| Bug fix | `@database/debugging-notes.md`, affected source file, `@tests/` |
| Documentation | `@candidate-info.md`, `@design-notes.md`, `@ai-prompts/` |
| Deployment | `@conf/`, `@database/setup-notes.md` |
| Architecture review | `@.cursorrules`, `@requirements-analysis.md`, `@data-model.md` |

### 4.2 Prompt Logs for Continuity

After each substantive task, prompts are appended to `ai-prompts/<topic>.md`:

```markdown
## Prompt N:
**PROMPT SENT:**
<verbatim user prompt>

**AI RESPONSE SUMMARY:**
<what was generated>

**YOUR EVALUATION:** ✓ good / ✗ fixes / △ missing
```

This enables a new session to `@ai-prompts/silver-layer.md` and understand prior decisions (e.g., why LEFT JOIN was chosen over INNER JOIN).

### 4.3 Debugging Notes as Institutional Memory

`database/debugging-notes.md` captures runtime-specific fixes (UC volume paths, `array_filter` bug, ANSI cast). Future sessions reference this to avoid re-discovering CE-specific issues.

---

## 5. Cursor Plan Mode

### 5.1 When Plan Mode Was Used

- **Initial project decomposition** — breaking the assessment into Data Gen → Bronze → Silver → Gold → Dashboard → Tests
- **Silver layer design** — deciding on five modular DQ files vs. monolithic script
- **Architecture boundary enforcement** — confirming soft-quarantine before code generation

### 5.2 Plan Mode Output

Plan Mode produced checklist-style task lists that were then executed sequentially in Composer or Chat. The task breakdown is preserved in `tool-specific/cursor-workflow/task-breakdown.md`.

### 5.3 Architecture Boundary Enforcement

Before implementing each layer, Plan Mode was prompted with:

```
@spec.md @.cursorrules
Plan the silver layer implementation. Enforce:
- Soft quarantine (no row drops)
- LEFT OUTER JOIN for FK checks
- Modular Column-based DQ functions
- No UDFs
```

This front-loaded architectural constraints before any code was written.

---

## 6. Composer Agent

### 6.1 When Composer Was Used

- **Multi-file scaffolding** — bronze ingest suite (4 Python modules + 4 notebooks + 4 job JSONs)
- **Silver DQ modules** — five check files + orchestrator + notebook + job config
- **Gold layer** — four SQL files + Python executor + notebook + job config
- **Test suite** — conftest + integration + unit tests + notebook wrappers

### 6.2 Composer + Context Tags

Composer sessions always started with:

```
@spec.md @.cursorrules @src/<related-layer>/
```

This ensured generated files followed existing naming conventions, import patterns, and architecture rules.

---

## 7. Chat for Targeted Refactoring

Chat mode was used for:

- Single-file bug fixes (`array_filter` replacement)
- Documentation updates
- Prompt log appends
- Credential/path troubleshooting
- Test threshold adjustments

Chat is preferred when the change scope is 1–2 files and architectural decisions are already settled.

---

## 8. Context Refresh Checklist

When resuming work in a new session:

1. Read `.cursorrules` (auto-applied)
2. `@spec.md` for schema/defect contract
3. `@ai-prompts/<relevant-topic>.md` for prior decisions
4. `@database/debugging-notes.md` if touching Databricks runtime
5. `@tests/` if modifying DQ logic
6. `@conf/` if changing deployment

---

## 9. Context Anti-Patterns Avoided

| Anti-Pattern | Why Avoided | Alternative |
|---|---|---|
| Relying on chat memory alone | Sessions don't persist context | `@` tags + prompt logs |
| Skipping `.cursorrules` | AI reverts to INNER JOIN / UDF defaults | Always-on workspace rules |
| Monolithic prompts | Context window overflow | Layer-by-layer with targeted `@` tags |
| Undocumented rejections | Same mistake repeated | Log ✗ evaluations in `ai-prompts/` |

---

## 10. Recommended Context Setup for Similar Projects

1. Create `.cursorrules` **before** any code generation
2. Write `spec.md` with schemas and test data contracts
3. Establish `ai-prompts/` logging from prompt 1
4. Use Plan Mode for decomposition, Composer for scaffolding, Chat for fixes
5. Maintain `database/debugging-notes.md` for runtime-specific discoveries
6. Tag `@tests/` whenever changing DQ or ingest logic
