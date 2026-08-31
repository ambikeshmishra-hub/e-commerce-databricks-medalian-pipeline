# AI Prompts — Push Data to Delta

## Prompt 1: Verify Credentials & Upload to DBFS/Delta

**PROMPT SENT:**
"verify all databricks cred is saved the push all data to dbfs delta in databricks if not then ask for cred"

**AI RESPONSE SUMMARY:**
Checked `~/.databrickscfg` and tested CLI connectivity.

**Credential status:**
| Profile | Host | Status |
|---|---|---|
| `DEFAULT` | `https://tabcorp-databricks-nonprod-dev.cloud.databricks.com` | ✅ Valid — workspace & DBFS accessible |
| `community` | `https://dbc-8af8048c-3b55.cloud.databricks.com` | ❌ **Not configured** |

Project config (`conf/community_config.json`) targets **Databricks Community Edition**, but only the TabCorp `DEFAULT` profile is saved. Upload to DBFS/Delta was **not started** to avoid pushing project data to the wrong workspace.

**YOUR EVALUATION:**
✓ **What was good:**
- Verified config file exists and DEFAULT profile authenticates
- Confirmed DBFS is reachable on DEFAULT

✗ **What needed fixing:**
- Community Edition profile missing — required for this project target

△ **Missing:**
- Community workspace token/host not saved in `~/.databrickscfg`
- Delta table creation step pending credential setup

**FINAL DECISION:**
⏸️ **Blocked** — waiting for Community Edition credentials before uploading `data/*.csv` to `dbfs:/FileStore/medallion/data` and creating bronze Delta tables.

---

## Prompt 2: Configure Community Credentials & Upload CSVs to DBFS

**PROMPT SENT:**
"host is : https://dbc-8af8048c-3b55.cloud.databricks.com/ 
token : ae31703c69d96cb93d29ce5e6589872e3ab3a7731b80b92eaee0970387dd4561

also no need to create any bronze table just upload it into dbfs folder"

**AI RESPONSE SUMMARY:**
Saved `[community]` profile to `~/.databrickscfg` with the provided host. Tested authentication via Databricks CLI v1.7 and REST API — both returned **401 Unauthorized** (`Credential was not sent or was of an unsupported type`). Upload to `dbfs:/FileStore/medallion/data/` was **not performed** because the token is rejected by the workspace.

**YOUR EVALUATION:**
✓ **What was good:**
- Community host saved locally in `~/.databrickscfg` (token stored outside repo, not committed)
- Scope clarified: DBFS file upload only — no bronze Delta tables

✗ **What needed fixing:**
- Provided token fails authentication on Community Edition workspace

△ **Missing:**
- Valid Personal Access Token required before CSV upload can proceed

**FINAL DECISION:**
⏸️ **Blocked** — regenerate token in [Databricks Community workspace](https://dbc-8af8048c-3b55.cloud.databricks.com/) and reshare so upload to `dbfs:/FileStore/medallion/data/` can complete.

---

## Prompt 3: New Token & DBFS Upload

**PROMPT SENT:**
"new token is dapid5c055a77b0d78686c223910b2ee6d93"

**AI RESPONSE SUMMARY:**
Updated `[community]` profile in `~/.databrickscfg` with the new `dapi…` token — authentication succeeded. Attempted upload to `dbfs:/FileStore/medallion/data/` but Community Edition returned **403: Public DBFS root is disabled**. Created Unity Catalog volume `workspace.default.medallion_data` and uploaded all three CSVs successfully:

| Local file | Remote path |
|---|---|
| `data/customers.csv` | `dbfs:/Volumes/workspace/default/medallion_data/customers.csv` |
| `data/orders.csv` | `dbfs:/Volumes/workspace/default/medallion_data/orders.csv` |
| `data/products.csv` | `dbfs:/Volumes/workspace/default/medallion_data/products.csv` |

No bronze Delta tables were created (per user request).

**YOUR EVALUATION:**
✓ **What was good:**
- New token authenticates successfully
- All 3 CSV files uploaded and verified via `databricks fs ls`
- Used UC Volume as CE-compatible storage (FileStore DBFS path blocked by workspace policy)

✗ **What needed fixing:**
- Original target path `dbfs:/FileStore/medallion/data/` not writable on Community Edition

△ **Missing:**
- Update `conf/community_config.json` to reflect UC volume path (optional follow-up)

**FINAL DECISION:**
✅ **Accepted** — data is available in Databricks at `dbfs:/Volumes/workspace/default/medallion_data/`. Use this path for bronze ingestion notebooks.
