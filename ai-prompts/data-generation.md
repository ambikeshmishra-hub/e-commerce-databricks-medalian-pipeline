# AI Prompts — Data Generation

## Prompt 1: Initial Data Generation Script

**PROMPT SENT:**
"Generate Python script to create realistic e-commerce customer data.
I need 10,000 rows with these fields: customer_id (INT), customer_name (STRING),
email (STRING), country (STRING), signup_date (DATE between 2020-2024),
customer_segment (Premium/Standard/Basic), lifetime_value (DECIMAL).
Include realistic values like actual names, valid email formats, and random dates."

**AI RESPONSE SUMMARY:**
[Cursor generated Python script using faker library to create realistic data]

**YOUR EVALUATION:**
✓ **What was good:**
- Used faker for realistic names and emails
- Date range correct (2020-2026)
- Customer segments randomized properly

✗ **What needed fixing:**
- Some customers had signup_date in future
- No intentional quality issues (needed 50 NULL emails, 10 duplicates, etc.)
- Missing lifetime_value calculations

△ **Missing:**
- No NULL values as needed for quality testing
