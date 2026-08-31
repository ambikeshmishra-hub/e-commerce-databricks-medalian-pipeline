# AI Prompts — Project Architecture

## Prompt 1: 

**PROMPT SENT:**
"Act as a Lead Data Engineer. Initialize this project repository by automatically generating the entire required folder structure and creating blank placeholder files for every single artifact mentioned in our requirements.  
Create these directories and blank files:
Root files: .cursorrules, README.md, candidate-info.md, tool-workflow.md, requirements-analysis.md, design-notes.md, data-model.md, data-quality-strategy.md  
tool-specific/cursor-workflow/: project-context.md, spec.md, cursor-rules-or-instructions.md, task-breakdown.md  src/data_generation/: generate_sample_data.py, DATA_GENERATION_NOTES.md  
src/bronze/: 01_ingest_customers.py, 02_ingest_orders.py, 03_ingest_products.py, ingest_all.py  
src/silver/: 01_quality_completeness.py, 02_quality_uniqueness.py, 03_quality_type_validation.py, 04_quality_referential_integrity.py, 05_quality_business_logic.py, create_silver_tables.py  src/gold/: 01_sales_by_product.sql, 02_revenue_by_customer.sql, 03_daily_weekly_trends.sql, 04_customer_segmentation.sql, create_gold_tables.py  src/dashboard/: dashboard_queries.sql, DASHBOARD_GUIDE.md  
data/: customers.csv, orders.csv, products.csv  database/: schema.sql, seed-data-notes.md, setup-notes.md, debugging-notes.md, reflection.md, final-ai-usage-summary.md  
ai-prompts/: data-generation.md, bronze-layer.md, silver-layer.md, gold-layer.md, dashboard.md, debugging.md, documentation.md  
Do not generate code yet—simply create all folders and touch/create these blank files so the full workspace map is initialized."

**AI RESPONSE SUMMARY:**
The repository workspace map is initialized. All directories and blank placeholder files are in place — no code or content was added.

Workspace Map
databricks-medallion-pipeline/
├── .cursorrules
├── README.md
├── candidate-info.md
├── tool-workflow.md
├── requirements-analysis.md
├── design-notes.md
├── data-model.md
├── data-quality-strategy.md
│
├── tool-specific/
│   └── cursor-workflow/
│       ├── project-context.md
│       ├── spec.md
│       ├── cursor-rules-or-instructions.md
│       └── task-breakdown.md
│
├── src/
│   ├── data_generation/
│   │   ├── generate_sample_data.py
│   │   └── DATA_GENERATION_NOTES.md
│   ├── bronze/
│   │   ├── 01_ingest_customers.py
│   │   ├── 02_ingest_orders.py
│   │   ├── 03_ingest_products.py
│   │   └── ingest_all.py
│   ├── silver/
│   │   ├── 01_quality_completeness.py
│   │   ├── 02_quality_uniqueness.py
│   │   ├── 03_quality_type_validation.py
│   │   ├── 04_quality_referential_integrity.py
│   │   ├── 05_quality_business_logic.py
│   │   └── create_silver_tables.py
│   ├── gold/
│   │   ├── 01_sales_by_product.sql
│   │   ├── 02_revenue_by_customer.sql
│   │   ├── 03_daily_weekly_trends.sql
│   │   ├── 04_customer_segmentation.sql
│   │   └── create_gold_tables.py
│   └── dashboard/
│       ├── dashboard_queries.sql
│       └── DASHBOARD_GUIDE.md
│
├── data/
│   ├── customers.csv
│   ├── orders.csv
│   └── products.csv
│
├── database/
│   ├── schema.sql
│   ├── seed-data-notes.md
│   ├── setup-notes.md
│   ├── debugging-notes.md
│   ├── reflection.md
│   └── final-ai-usage-summary.md
│
└── ai-prompts/
    ├── data-generation.md
    ├── bronze-layer.md
    ├── silver-layer.md
    ├── gold-layer.md
    ├── dashboard.md
    ├── debugging.md
    └── documentation.md
Totals: 8 root files · 4 tool-specific files · 18 src/ artifacts · 3 data files · 6 database files · 7 AI prompt files — 46 blank files across 9 directories.



**YOUR EVALUATION:**
✓ **What was good:**
- Used proper provided folder directory
- created all blank file no slef assumption code

△ **Missing:**
- Strictly provide all folder and file directory so no missing


# AI Prompts — GitHub

## Prompt 2: 

**PROMPT SENT:**
"add below git remote repo 
https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git and push the project to main repo"
**AI RESPONSE SUMMARY:**
"Completed
Initial commit on main — 48 files, commit 0f8a542:

Initialize medallion pipeline project structure.

Remote added:

origin → https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git
Push blocked (authentication)
The push did not complete from this environment — GitHub needs credentials that aren’t available here (HTTPS prompted for username; SSH returned Permission denied (publickey)).

Finish the push locally"
**My Action with Cursor:**
"Run below commands 
    1. -v && git branch -a && git log --oneline -3 2>/dev/null || echo "No commits yet"
    2. cd /Users/ambikeshmishra/databricks-medallion-pipeline && git add -A && git commit -m && git remote add origin https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git && git push -u origin main
    3. cd /Users/ambikeshmishra/databricks-medallion-pipeline && git remote add origin https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git 2>/dev/null || git remote set-url origin https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git && git remote -v && git push -u origin main
    4. which gh && gh auth status 2>&1; git config --get credential.helper 2>/dev/null; ls -la ~/.ssh/*.pub 2>/dev/null | head -5
    5. cd /Users/ambikeshmishra/databricks-medallion-pipeline && git remote set-url origin git@github.com:ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git && git push -u origin main
    6. mkdir -p ~/.ssh && ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null && cd /Users/ambikeshmishra/databricks-medallion-pipeline && git push -u origin main
    7. env | grep -iE 'github|git_' 2>/dev/null; git config --list 2>/dev/null | grep -iE 'user|credential|github' | head -10
    8. cd /Users/ambikeshmishra/databricks-medallion-pipeline && git remote set-url origin https://github.com/ambikeshmishra-hub/e-commerce-databricks-medalian-pipeline.git && git remote -v && git status && git log --oneline -1 
    " 
**YOUR EVALUATION:**
✓ **What was good:**
- Staged & commited the changes
- Tracked all modified files
△ **Missing:**
- Unable to push/autheticate due to otp validation

**My Manual Action:**
- Athenticated manually and pushed the code




## Prompt 3: 

**PROMPT SENT:**
install pip install databricks-cli faker pandas numpy and setup databricks using tokes as 'dapif7dd770a78d503340bf2a2171814d8a2' and url is https://dbc-8af8048c-3b55.cloud.databricks.com/  and setup it accordingly that we need to execute it on databricks community edition

**AI RESPONSE SUMMARY:**

105 x 16
install pip install databricks-cli faker pandas numpy and setup databricks using tokes as 'dapif7dd770a78d503340bf2a2171814d8a2' and url is 
dbc-8af8048c-3b55.cloud.databricks.com
  and setup it accordingly that we need to execute it on databricks community edition

Agent

  Downloading urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
Collecting tzdata (from faker>=24.0.0->-r requirements.txt (line 2))
  Downloading tzdata-2026.3-py2.py3-none-any.whl.metadata (1.4 kB)
Collecting python-dateutil>=2.8.2 (from pandas>=2.0.0->-r requirements.txt (line 3))
  Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Packages installed. Configuring Databricks CLI and verifying the connection.