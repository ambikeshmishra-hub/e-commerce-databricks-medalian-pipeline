# Data Quality Strategy — E-Commerce Medallion Pipeline

Comprehensive data quality framework for the Silver layer soft-quarantine model, aligned with `tool-specific/cursor-workflow/spec.md` and implemented in `src/silver/`.

---

## 1. Strategy Overview

### 1.1 Philosophy

| Principle | Implementation |
|---|---|
| **Detect, don't delete** | Flag bad rows with `dq_errors` and `quality_check_result = 'FAIL'` |
| **Preserve evidence** | Bronze/silver row-count parity maintained |
| **Clean analytics boundary** | Gold reads `PASS` only |
| **Modular rules** | One Python module per DQ category |
| **Vectorized execution** | Native PySpark `Column` expressions—no UDFs |

### 1.2 Scope

**In scope (silver_orders):**

- Completeness of `customer_id`, `product_id`
- Uniqueness of `order_id`
- Numeric positivity of `quantity`, `unit_price`, `total_amount`
- Referential integrity of `customer_id` → `bronze_customers`, `product_id` → `bronze_products`
- Business rule: `payment_date >= order_date`

**Out of scope (current phase):**

- Silver DQ on `bronze_customers` and `bronze_products` (defects exist in seed data but are not validated in pipeline)
- Email format validation, segment enum validation, cost-vs-price checks (injected in seed data for future modules)

---

## 2. Quality Check Categories

### 2.1 Completeness

**Module:** `src/silver/01_quality_completeness.py`  
**Function:** `check_completeness(column_name, error_tag)`

| Rule ID | Column | Condition | Error Tag | Seed Defects |
|---|---|---|---|---|
| CMP-01 | `customer_id` | `IS NULL` | `NULL_CUSTOMER_ID` | 100 rows (O01) |
| CMP-02 | `product_id` | `IS NULL` | `NULL_PRODUCT_ID` | 200 rows (O02) |

**Threshold:** > 99% of order rows have non-null `customer_id` and `product_id`.

**Implementation:**

```python
when(col(column_name).isNull(), lit(error_tag))
```

---

### 2.2 Uniqueness

**Module:** `src/silver/02_quality_uniqueness.py`  
**Functions:** `flag_duplicates()`, `check_uniqueness()`

| Rule ID | Column | Condition | Error Tag | Seed Defects |
|---|---|---|---|---|
| UNQ-01 | `order_id` | `count(*) OVER (PARTITION BY order_id) > 1` | `DUPLICATE_ORDER_ID` | 20 rows (O05) |

**Threshold:** 100% uniqueness among `PASS` rows.

**Implementation:**

```python
duplicate_window = Window.partitionBy(id_col)
df.withColumn("row_occurrence_count", count(col(id_col)).over(duplicate_window))
# ...
when(col("row_occurrence_count") > 1, lit("DUPLICATE_ORDER_ID"))
```

**Note:** Window-based counting preserves all rows (no `dropDuplicates()`).

---

### 2.3 Type Validation

**Module:** `src/silver/03_quality_type_validation.py`  
**Function:** `check_numeric_positive(column_name, error_tag)`

| Rule ID | Column | Condition | Error Tag |
|---|---|---|---|
| TYP-01 | `quantity` | `try_cast AS DOUBLE <= 0` | `NON_POSITIVE_QUANTITY` |
| TYP-02 | `unit_price` | `try_cast AS DOUBLE <= 0` | `NON_POSITIVE_UNIT_PRICE` |
| TYP-03 | `total_amount` | `try_cast AS DOUBLE <= 0` | `NON_POSITIVE_TOTAL_AMOUNT` |

**Threshold:** > 99% of numeric fields castable and positive.

**Implementation:**

```python
numeric_value = expr(f"try_cast(`{column_name}` AS DOUBLE)")
when(numeric_value.isNotNull() & (numeric_value <= 0), lit(error_tag))
```

**Design note:** `try_cast` prevents ANSI mode exceptions on `"N/A"` quantity strings (O09). Cast failures return NULL and skip the positivity check—raw value preserved in bronze/silver.

**Related seed defects (not directly caught by current rules):**

| Code | Defect | Rows |
|---|---|---|
| O09 | Non-numeric quantity (`"N/A"`) | 20 |
| P05 | Non-numeric price (`"INVALID"`) | 20 |

---

### 2.4 Referential Integrity

**Module:** `src/silver/04_quality_referential_integrity.py`  
**Functions:** `check_foreign_key()`, `flag_invalid_fk()`

| Rule ID | FK Column | Parent Table | Parent PK | Error Tag | Seed Defects |
|---|---|---|---|---|---|
| REF-01 | `customer_id` | `bronze_customers` | `customer_id` | `INVALID_CUSTOMER_ID_FK` | 50 rows (O03) |
| REF-02 | `product_id` | `bronze_products` | `product_id` | `INVALID_PRODUCT_ID_FK` | 30 rows (O04) |

**Threshold:** > 99.9% FK validity (non-null FKs resolve to existing parent keys).

**Join type:** **LEFT OUTER JOIN** (mandatory per `.cursorrules`).

**Implementation:**

```python
parent_keys = parent_df.select(col(parent_pk_col).alias(alias_col)).distinct()
child_df.join(parent_keys, col(fk_col) == col(alias_col), "left")
# ...
when(col(fk_col).isNotNull() & col(alias_col).isNull(), lit(error_tag))
```

**Rejected pattern:** INNER JOIN silently drops orphan rows—discovered during AI code review and overridden.

---

### 2.5 Business Logic

**Module:** `src/silver/05_quality_business_logic.py`  
**Function:** `check_order_payment_dates()`

| Rule ID | Condition | Error Tag | Seed Defects |
|---|---|---|---|
| BUS-01 | `payment_date < order_date` (when payment_date not null) | `PAYMENT_BEFORE_ORDER_DATE` | 10 rows (O07) |

**Threshold:** 100% of PASS rows have `payment_date >= order_date`.

**Related seed defects (not in current silver rules):**

| Code | Defect | Rows | Future Rule |
|---|---|---|---|
| O06 | `total_amount != quantity × unit_price` | 15 | Amount reconciliation |
| O08 | Invalid `order_status` (`UNKNOWN`) | 10 | Enum validation |
| O10 | Future `order_date` | 10 | Date range check |

---

## 3. Threshold Metrics

| Category | Metric | Target | Measurement |
|---|---|---|---|
| Completeness | % non-null `customer_id` AND `product_id` | > 99% | `1 - (null_fk_count / total_rows)` |
| Uniqueness | % unique `order_id` among all rows | Duplicates flagged, not dropped | Count of `DUPLICATE_ORDER_ID` tags |
| FK Validity | % non-null FKs with parent match | > 99.9% | `1 - (orphan_fk_count / non_null_fk_count)` |
| Type Validation | % positive numeric amounts | > 99% | Count of `NON_POSITIVE_*` tags |
| Business Logic | % valid payment timing | > 99.9% | Count of `PAYMENT_BEFORE_ORDER_DATE` tags |
| Overall PASS rate | % rows with empty `dq_errors` | > 98% | `passed_rows / total_rows` |

**Observed results (50,000 orders, 700 injected defects):**

- Quarantined rows: **> 400** (integration test threshold)
- PASS rows: **> 49,000** (~99%+)
- Bronze/silver parity: **100%**

---

## 4. Metrics Reporting Format

### 4.1 Pipeline Output

After `create_silver_tables.py` completes, stdout displays:

```
============================================================
Data Quality Metrics Summary — silver_orders
============================================================
Total rows processed:          50,000
Passed rows:                   49,5xx ( 99.xx%)
Quarantined bad rows:             xxx (  0.xx%)
============================================================
```

### 4.2 Programmatic Summary

`DqMetricsSummary` dataclass in `create_silver_tables.py`:

| Field | Type | Description |
|---|---|---|
| `total_rows` | int | All silver rows |
| `passed_rows` | int | Rows where `quality_check_result = 'PASS'` |
| `quarantined_rows` | int | `total_rows - passed_rows` |
| `passed_pct` | float | `(passed_rows / total_rows) × 100` |
| `quarantined_pct` | float | `(quarantined_rows / total_rows) × 100` |

### 4.3 Ad-Hoc SQL Queries

```sql
-- Pass/fail distribution
SELECT quality_check_result, COUNT(*) AS row_count
FROM workspace.silver.silver_orders
GROUP BY quality_check_result;

-- Error tag frequency (exploded)
SELECT error_tag, COUNT(*) AS occurrences
FROM workspace.silver.silver_orders
LATERAL VIEW EXPLODE(dq_errors) e AS error_tag
WHERE quality_check_result = 'FAIL'
GROUP BY error_tag
ORDER BY occurrences DESC;
```

---

## 5. Intentional Defect Manifest (~700 Rows)

### 5.1 Spec-Required Defects (460 rows)

| Code | Table | Count | Description | Silver Rule |
|---|---|---|---|---|
| C01 | customers | 50 | NULL email | *(not in silver scope)* |
| C02 | customers | 10 | Duplicate `customer_id` | *(not in silver scope)* |
| O01 | orders | 100 | NULL `customer_id` | `NULL_CUSTOMER_ID` |
| O02 | orders | 200 | NULL `product_id` | `NULL_PRODUCT_ID` |
| O03 | orders | 50 | Invalid `customer_id` (orphan FK) | `INVALID_CUSTOMER_ID_FK` |
| O04 | orders | 30 | Invalid `product_id` (orphan FK) | `INVALID_PRODUCT_ID_FK` |
| O05 | orders | 20 | Duplicate `order_id` | `DUPLICATE_ORDER_ID` |
| | | **460** | | |

### 5.2 Supplemental Defects (240 rows)

| Code | Table | Count | Description | Silver Rule |
|---|---|---|---|---|
| C03 | customers | 15 | NULL `customer_name` | *(future)* |
| C04 | customers | 15 | Invalid email format | *(future)* |
| C05 | customers | 10 | Future `signup_date` | *(future)* |
| C06 | customers | 15 | Invalid `customer_segment` (`VIP`) | *(future)* |
| C07 | customers | 15 | Negative `lifetime_value` | *(future)* |
| P01 | products | 20 | NULL `product_name` | *(future)* |
| P02 | products | 15 | Duplicate `product_id` | *(future)* |
| P03 | products | 15 | Negative `stock_quantity` | *(future)* |
| P04 | products | 20 | NULL `category` | *(future)* |
| P05 | products | 20 | Invalid price (`INVALID`) | *(future)* |
| P06 | products | 15 | Cost > price | *(future)* |
| O06 | orders | 15 | `total_amount` mismatch | *(future)* |
| O07 | orders | 10 | `payment_date` before `order_date` | `PAYMENT_BEFORE_ORDER_DATE` |
| O08 | orders | 10 | Invalid `order_status` | *(future)* |
| O09 | orders | 20 | Non-numeric `quantity` | *(partial—try_cast)* |
| O10 | orders | 10 | Future `order_date` | *(future)* |
| | | **240** | | |

**Grand total: 700 intentional defects** (verified by `ISSUE_MANIFEST` in `generate_sample_data.py`).

### 5.3 Overlap & Multi-Tag Rows

A single order row can accumulate **multiple** `dq_errors` tags when it violates more than one rule (e.g., NULL `customer_id` AND duplicate `order_id`). This is why quarantined row count may be **less than 700** while total defect injections equal 700.

---

## 6. Quarantine vs. Gold Filter

```
                    ┌─────────────────────────────────────┐
  bronze_orders     │           silver_orders              │
  (all rows)   ───▶ │  PASS: dq_errors = []              │───▶ gold_* (analytics)
                    │  FAIL: dq_errors = [tag1, tag2, …] │     (PASS only)
                    │  (rows retained, never dropped)    │
                    └─────────────────────────────────────┘
```

---

## 7. Testing & Validation

| Test | File | Assertion |
|---|---|---|
| Row parity | `test_pipeline.py` | `silver_count == bronze_count` |
| Anomaly detection | `test_pipeline.py` | `FAIL_count > 400` |
| PASS integrity | `test_pipeline.py` | No PASS row has non-empty `dq_errors` |
| Gold purity | `test_pipeline.py` | Revenue > 0, valid segments |
| Unit: completeness | `test_silver_rules.py` | Null detection |
| Unit: uniqueness | `test_silver_rules.py` | Duplicate flagging |
| Unit: FK | `test_silver_rules.py` | Orphan detection via LEFT JOIN |
| Unit: business logic | `test_silver_rules.py` | Payment date ordering |

---

## 8. Future Enhancements

| Enhancement | Tool / Pattern |
|---|---|
| Customer/product silver DQ | Extend `create_silver_tables.py` |
| Great Expectations suites | `expect_column_values_to_not_be_null`, `expect_foreign_key_to_be_present` |
| DLT `CONSTRAINT` / `EXPECT` | Declarative DQ in pipeline DAG |
| DQ dashboard | Monitor `quarantined_pct` over time |
| Alerting | Trigger when `quarantined_pct` exceeds SLA threshold |
