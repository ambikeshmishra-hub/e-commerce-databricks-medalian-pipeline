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
