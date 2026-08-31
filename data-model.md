# Data Model — E-Commerce Medallion Pipeline

Full schema definitions for all pipeline-managed tables in Unity Catalog catalog `workspace`.

---

## 1. Entity Relationship Overview

```
bronze_customers (customer_id PK)
       │
       │ 1:N
       ▼
bronze_orders (order_id) ──N:1──▶ bronze_products (product_id PK)
       │
       │ DQ enrichment
       ▼
silver_orders (+ dq_errors, quality_check_result)
       │
       │ PASS filter
       ▼
gold_* marts (aggregated)
```

---

## 2. Source CSV Schemas

### 2.1 `customers.csv`

| Column | Logical Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `customer_id` | INT | **PK** | No (baseline) | Surrogate customer identifier (1..10,000 base; duplicates injected) |
| `customer_name` | STRING | | Yes (injected nulls) | Full name of the customer |
| `email` | STRING | | Yes (injected nulls) | Email address |
| `country` | STRING | | No | Country of residence (Faker-generated) |
| `signup_date` | DATE | | No (baseline) | Account creation date (2020-01-01 to 2024-12-31) |
| `customer_segment` | STRING | | No (baseline) | `Premium`, `Standard`, or `Basic` |
| `lifetime_value` | DECIMAL(18,2) | | No (baseline) | Historical customer value in USD |

### 2.2 `products.csv`

| Column | Logical Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `product_id` | INT | **PK** | No (baseline) | Surrogate product identifier (1..1,000 base; duplicates injected) |
| `product_name` | STRING | | Yes (injected nulls) | Product display name |
| `category` | STRING | | Yes (injected nulls) | One of seven categories (Electronics, Clothing, etc.) |
| `price` | DECIMAL(18,2) | | No (baseline) | List price in USD ($5–$500) |
| `cost` | DECIMAL(18,2) | | No | Unit cost in USD (35–75% of price) |
| `stock_quantity` | INT | | No (baseline) | Units on hand (0–499; negative values injected) |
| `reorder_level` | INT | | No | Reorder threshold (10–99) |

### 2.3 `orders.csv`

| Column | Logical Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `order_id` | INT | **PK** (intended) | No | Order identifier (1..50,000 base; duplicates injected) |
| `customer_id` | INT | **FK → customers** | Yes (injected nulls) | Reference to `customers.customer_id` |
| `order_date` | DATE | | No (baseline) | Date order was placed |
| `product_id` | INT | **FK → products** | Yes (injected nulls) | Reference to `products.product_id` |
| `quantity` | INT | | No (baseline) | Units ordered (1–5; `"N/A"` injected) |
| `unit_price` | DECIMAL(18,2) | | No | Price per unit at time of order |
| `total_amount` | DECIMAL(18,2) | | No | Line total (`quantity × unit_price`; mismatches injected) |
| `order_status` | STRING | | No (baseline) | `Pending`, `Shipped`, `Delivered`, `Cancelled`, `Returned` |
| `payment_date` | DATE | | No (baseline) | Payment settlement date (0–14 days after order) |

---

## 3. Bronze Layer Schemas

Bronze tables = source CSV columns + audit metadata. Types inferred by Spark CSV reader.

### 3.1 `workspace.bronze.bronze_customers`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `customer_id` | INT | **PK** | Yes | Raw customer ID from CSV |
| `customer_name` | STRING | | Yes | Raw customer name |
| `email` | STRING | | Yes | Raw email |
| `country` | STRING | | Yes | Raw country |
| `signup_date` | DATE | | Yes | Raw signup date |
| `customer_segment` | STRING | | Yes | Raw segment value |
| `lifetime_value` | DOUBLE | | Yes | Raw lifetime value |
| `_ingested_at` | TIMESTAMP | | No | Ingestion timestamp (pipeline-generated) |
| `_source_file` | STRING | | No | Source file path from `_metadata.file_path` |

**Row count (generated):** ~10,011 (10,000 base + 10 duplicate rows)

### 3.2 `workspace.bronze.bronze_products`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `product_id` | INT | **PK** | Yes | Raw product ID |
| `product_name` | STRING | | Yes | Raw product name |
| `category` | STRING | | Yes | Raw category |
| `price` | STRING/DOUBLE | | Yes | Raw price (may be `"INVALID"` string) |
| `cost` | DOUBLE | | Yes | Raw cost |
| `stock_quantity` | INT | | Yes | Raw stock count |
| `reorder_level` | INT | | Yes | Raw reorder level |
| `_ingested_at` | TIMESTAMP | | No | Ingestion timestamp |
| `_source_file` | STRING | | No | Source file path |

**Row count (generated):** ~1,016 (1,000 base + 15 duplicate rows)

### 3.3 `workspace.bronze.bronze_orders`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `order_id` | INT | **PK** (intended) | Yes | Raw order ID |
| `customer_id` | INT | **FK** | Yes | Raw customer FK |
| `order_date` | DATE | | Yes | Raw order date |
| `product_id` | INT | **FK** | Yes | Raw product FK |
| `quantity` | INT/STRING | | Yes | Raw quantity (may be `"N/A"`) |
| `unit_price` | DOUBLE | | Yes | Raw unit price |
| `total_amount` | DOUBLE | | Yes | Raw line total |
| `order_status` | STRING | | Yes | Raw order status |
| `payment_date` | DATE | | Yes | Raw payment date |
| `_ingested_at` | TIMESTAMP | | No | Ingestion timestamp |
| `_source_file` | STRING | | No | Source file path |

**Row count (generated):** 50,000

---

## 4. Silver Layer Schema

### 4.1 `workspace.silver.silver_orders`

All `bronze_orders` columns plus DQ enrichment columns. Temporary join columns are dropped before persist.

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `order_id` | INT | **PK** (intended) | Yes | Order identifier from bronze |
| `customer_id` | INT | **FK → bronze_customers** | Yes | Customer foreign key |
| `order_date` | DATE | | Yes | Order placement date |
| `product_id` | INT | **FK → bronze_products** | Yes | Product foreign key |
| `quantity` | INT/STRING | | Yes | Order quantity |
| `unit_price` | DOUBLE | | Yes | Unit price |
| `total_amount` | DOUBLE | | Yes | Line total amount |
| `order_status` | STRING | | Yes | Order lifecycle status |
| `payment_date` | DATE | | Yes | Payment date |
| `_ingested_at` | TIMESTAMP | | Yes | Bronze audit: ingestion time |
| `_source_file` | STRING | | Yes | Bronze audit: source path |
| `dq_errors` | ARRAY&lt;STRING&gt; | | No | List of DQ error tags; empty array on PASS |
| `quality_check_result` | STRING | | No | `'PASS'` or `'FAIL'` |

**Constraints (logical, not enforced by Delta):**

- `quality_check_result = 'PASS'` ⟺ `size(dq_errors) = 0`
- Row count must equal `bronze_orders` row count

**Possible `dq_errors` values:**

| Error Tag | Rule Module |
|---|---|
| `NULL_CUSTOMER_ID` | Completeness |
| `NULL_PRODUCT_ID` | Completeness |
| `DUPLICATE_ORDER_ID` | Uniqueness |
| `NON_POSITIVE_QUANTITY` | Type Validation |
| `NON_POSITIVE_UNIT_PRICE` | Type Validation |
| `NON_POSITIVE_TOTAL_AMOUNT` | Type Validation |
| `INVALID_CUSTOMER_ID_FK` | Referential Integrity |
| `INVALID_PRODUCT_ID_FK` | Referential Integrity |
| `PAYMENT_BEFORE_ORDER_DATE` | Business Logic |

---

## 5. Gold Layer Schemas

All gold tables source `silver_orders` WHERE `quality_check_result = 'PASS'`.

### 5.1 `workspace.gold.gold_sales_by_product`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `product_id` | INT | **PK** | No | Product identifier |
| `product_name` | STRING | | No | Product name from bronze_products |
| `category` | STRING | | No | Product category |
| `total_orders` | BIGINT | | No | Count of PASS order lines for this product |
| `total_revenue` | DOUBLE | | No | Sum of `total_amount` (rounded to 2 dp) |
| `avg_order_value` | DOUBLE | | No | Average `total_amount` per order line |

### 5.2 `workspace.gold.gold_revenue_by_customer`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `customer_id` | INT | **PK** | No | Customer identifier |
| `customer_name` | STRING | | No | Customer name from bronze_customers |
| `customer_segment` | STRING | | No | Source segment (`Premium`/`Standard`/`Basic`) |
| `total_orders` | BIGINT | | No | Count of PASS order lines |
| `total_revenue` | DOUBLE | | No | Sum of `total_amount` |
| `avg_order_value` | DOUBLE | | No | Average order line value |
| `lifetime_value_actual` | DOUBLE | | No | Average of source `lifetime_value` from bronze |

### 5.3 `workspace.gold.gold_daily_weekly_trends`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `order_date` | DATE | **PK** (partial) | No | Calendar date of orders |
| `order_week` | DATE | | No | Week start (`DATE_TRUNC('week', order_date)`) |
| `daily_order_count` | BIGINT | | No | Orders on that date |
| `daily_revenue` | DOUBLE | | No | Revenue on that date |

### 5.4 `workspace.gold.gold_customer_segmentation`

| Column | Spark Type | PK/FK | Nullable | Description |
|---|---|---|---|---|
| `segment_type` | STRING | **PK** | No | Behavioral segment: `High-Value`, `Repeat`, `One-Time`, `Inactive` |
| `customer_count` | BIGINT | | No | Distinct customers in segment |
| `avg_revenue` | DOUBLE | | No | Average per-customer revenue in segment |
| `total_revenue` | DOUBLE | | No | Total segment revenue |

**Segmentation rules (applied per customer from PASS orders):**

| Segment | Condition |
|---|---|
| `High-Value` | `total_revenue > 3000` |
| `Repeat` | `total_orders > 5` |
| `One-Time` | `total_orders = 1` |
| `Inactive` | All other customers with PASS orders |

---

## 6. Unity Catalog Namespace

| Schema | Purpose | Managed Tables |
|---|---|---|
| `workspace.bronze` | Raw ingest | 3 bronze tables |
| `workspace.silver` | DQ-enriched | 1 silver table (orders) |
| `workspace.gold` | Analytics marts | 4 gold tables |
| `workspace.default` | Shared assets | `medallion_data` volume (CSVs) |

---

## 7. Data Lineage Summary

```
customers.csv ──▶ bronze_customers ──┐
products.csv  ──▶ bronze_products  ──┼──▶ silver_orders ──▶ gold_* (PASS only)
orders.csv    ──▶ bronze_orders    ──┘
```

Metadata lineage: `_source_file` → UC volume path → `_ingested_at` → job execution timestamp.
