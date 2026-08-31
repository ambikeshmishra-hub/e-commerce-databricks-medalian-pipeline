# Data Generation Notes — `generate_sample_data.py`

Technical documentation for the synthetic CSV generator at `src/data_generation/generate_sample_data.py`.

---

## 1. Purpose

Generate three e-commerce CSV files (`customers.csv`, `orders.csv`, `products.csv`) with:

- Realistic baseline distributions (Faker + NumPy)
- **Exactly 700 intentional data-quality defects** for silver-layer validation
- Reproducible output via fixed random seed

---

## 2. Libraries

| Library | Version (pinned) | Purpose |
|---|---|---|
| **Pandas** | via `requirements.txt` | DataFrame construction and CSV export |
| **NumPy** | via `requirements.txt` | Random number generation, index selection |
| **Faker** | via `requirements.txt` | Synthetic names, emails, countries, product names |
| **random** (stdlib) | — | Seed synchronization with NumPy |
| **dataclasses** (stdlib) | — | `IssueSpec` defect manifest records |
| **pathlib** (stdlib) | — | Cross-platform path resolution |

---

## 3. Configuration Constants

| Constant | Value | Line | Purpose |
|---|---|---|---|
| `RANDOM_SEED` | `42` | 24 | Master seed for all RNG |
| `NUM_CUSTOMERS` | `10_000` | 25 | Base customer row count |
| `NUM_PRODUCTS` | `1_000` | 26 | Base product row count |
| `NUM_ORDERS` | `50_000` | 27 | Order row count |
| `CUSTOMER_SEGMENTS` | Premium/Standard/Basic | 29 | Valid segment enum |
| `ORDER_STATUSES` | 5 statuses | 30 | Valid order lifecycle states |
| `PRODUCT_CATEGORIES` | 7 categories | 31–39 | Valid product categories |
| `SEGMENT_LTV_RANGES` | Per-segment USD ranges | 41–45 | Lifetime value bounds |
| `PROJECT_ROOT` | `parents[2]` from `__file__` | 47 | Repo root resolution |
| `DATA_DIR` | `PROJECT_ROOT / "data"` | 48 | Output directory |
| `SIGNUP_START` | `2020-01-01` | 50 | Earliest signup date |
| `SIGNUP_END` | `2024-12-31` | 51 | Latest signup date |
| `ORDER_END` | `2025-12-31` | 52 | Latest order date |

---

## 4. Random Seed Strategy

```python
# Line 377-380 in main()
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
fake = Faker()
Faker.seed(RANDOM_SEED)
rng = _rng()  # np.random.default_rng(RANDOM_SEED)
```

| Generator | Seed | Scope |
|---|---|---|
| `random` | 42 | Python stdlib (legacy sync) |
| `numpy` | 42 | Index selection, distributions |
| `Faker` | 42 | Customer names, emails, countries |
| `Faker` (products) | 43 (`RANDOM_SEED + 1`) | Product names (line 155) |

**Reproducibility guarantee:** Running `python src/data_generation/generate_sample_data.py` twice produces identical CSV files.

---

## 5. Issue Manifest (`ISSUE_MANIFEST`)

Defined at lines 66–94 as a tuple of `IssueSpec` dataclass records:

```python
@dataclass(frozen=True)
class IssueSpec:
    code: str       # Unique defect code (C01, O01, P01, etc.)
    table: str      # Target table name
    count: int      # Number of rows affected
    description: str
```

### 5.1 Spec-Required Defects (460 rows)

| Code | Table | Count | Description | Injection Function |
|---|---|---|---|---|
| C01 | customers | 50 | NULL email | `inject_customer_issues()` L225–227 |
| C02 | customers | 10 | duplicate customer_id | `inject_customer_issues()` L229–231 |
| O01 | orders | 100 | NULL customer_id | `inject_order_issues()` L304–306 |
| O02 | orders | 200 | NULL product_id | `inject_order_issues()` L308–310 |
| O03 | orders | 50 | invalid customer_id (missing FK) | `inject_order_issues()` L312–314 |
| O04 | orders | 30 | invalid product_id (missing FK) | `inject_order_issues()` L316–318 |
| O05 | orders | 20 | duplicate order_id | `inject_order_issues()` L320–323 |

### 5.2 Supplemental Defects (240 rows)

| Code | Table | Count | Description | Injection Function |
|---|---|---|---|---|
| C03 | customers | 15 | NULL customer_name | `inject_customer_issues()` L233–235 |
| C04 | customers | 15 | invalid email format | `inject_customer_issues()` L237–239 |
| C05 | customers | 10 | future signup_date | `inject_customer_issues()` L241–243 |
| C06 | customers | 15 | invalid customer_segment | `inject_customer_issues()` L245–247 |
| C07 | customers | 15 | negative lifetime_value | `inject_customer_issues()` L249–251 |
| P01 | products | 20 | NULL product_name | `inject_product_issues()` L260–262 |
| P02 | products | 15 | duplicate product_id | `inject_product_issues()` L264–266 |
| P03 | products | 15 | negative stock_quantity | `inject_product_issues()` L268–270 |
| P04 | products | 20 | NULL category | `inject_product_issues()` L272–274 |
| P05 | products | 20 | invalid price (non-numeric) | `inject_product_issues()` L276–279 |
| P06 | products | 15 | cost greater than price | `inject_product_issues()` L281–284 |
| O06 | orders | 15 | total_amount != qty × price | `inject_order_issues()` L325–330 |
| O07 | orders | 10 | payment_date before order_date | `inject_order_issues()` L332–336 |
| O08 | orders | 10 | invalid order_status | `inject_order_issues()` L338–340 |
| O09 | orders | 20 | invalid quantity (non-numeric) | `inject_order_issues()` L342–345 |
| O10 | orders | 10 | future order_date | `inject_order_issues()` L347–349 |

**Total: 700 defects** (verified by `sum(spec.count for spec in ISSUE_MANIFEST)`)

---

## 6. Function-by-Function Breakdown

### 6.1 `_rng()` (Line 98–99)

Returns `np.random.default_rng(RANDOM_SEED)` — the primary RNG for index selection and distributions.

### 6.2 `_pick_indices(pool_size, count, rng)` (Lines 102–105)

Selects `count` unique random indices from `[0, pool_size)` without replacement. Raises `ValueError` if `count > pool_size`. Used by all injection functions to deterministically select which rows receive defects.

### 6.3 `_blank(value)` (Lines 108–118)

Renders Python `None` and `NaN` as empty strings for CSV export. Preserves date ISO format and integer formatting.

### 6.4 `_random_date(rng, start, end)` (Lines 121–124)

Returns a uniform random date between `start` and `end` inclusive.

### 6.5 `generate_customers(fake, rng)` (Lines 127–149)

**Baseline generation (10,000 rows):**

| Step | Lines | Logic |
|---|---|---|
| ID assignment | 129 | `np.arange(1, NUM_CUSTOMERS + 1)` |
| Segment assignment | 130 | Weighted: Premium 20%, Standard 50%, Basic 30% |
| Per-row generation | 133–147 | Faker name/email/country, random signup date, segment-correlated LTV |

**Output columns:** `customer_id`, `customer_name`, `email`, `country`, `signup_date`, `customer_segment`, `lifetime_value`

### 6.6 `generate_products(rng)` (Lines 152–174)

**Baseline generation (1,000 rows):**

| Step | Lines | Logic |
|---|---|---|
| Faker seed | 154–155 | `Faker.seed(RANDOM_SEED + 1)` for independent product names |
| Per-row generation | 158–172 | Random category, price $5–$500, cost 35–75% of price, stock 0–499, reorder 10–99 |

### 6.7 `generate_orders(customers, products, rng)` (Lines 177–218)

**Baseline generation (50,000 rows):**

| Step | Lines | Logic |
|---|---|---|
| Customer pool | 183 | All customer IDs from customers DataFrame |
| Product catalog | 184–187 | Product IDs + prices, dropna on price |
| Signup lookup | 189 | Map customer_id → signup_date |
| Per-order generation | 192–216 | Random customer, random product, qty 1–5, unit_price ±5%, order_date after signup, payment 0–14 days later, random status |

**Key constraint:** Orders only reference valid customer/product IDs at generation time. Defects are injected afterward.

### 6.8 `inject_customer_issues(customers, rng)` (Lines 221–253)

| Lines | Code | Defect | Count | Mechanism |
|---|---|---|---|---|
| 225–227 | C01 | NULL email | 50 | Set `email = None` at picked indices |
| 229–231 | C02 | Duplicate customer_id | 10 | Copy 10 rows and `pd.concat` (appends duplicates) |
| 233–235 | C03 | NULL customer_name | 15 | Set `customer_name = None` |
| 237–239 | C04 | Invalid email | 15 | Set `email = "not-an-email"` |
| 241–243 | C05 | Future signup_date | 10 | Set `signup_date = date(2027, 1, 1)` |
| 245–247 | C06 | Invalid segment | 15 | Set `customer_segment = "VIP"` |
| 249–251 | C07 | Negative LTV | 15 | Set `lifetime_value` to uniform(-500, -1) |

**Post-injection row count:** 10,000 + 10 = **10,011**

### 6.9 `inject_product_issues(products, rng)` (Lines 256–286)

| Lines | Code | Defect | Count | Mechanism |
|---|---|---|---|---|
| 260–262 | P01 | NULL product_name | 20 | Set `product_name = None` |
| 264–266 | P02 | Duplicate product_id | 15 | Copy 15 rows and `pd.concat` |
| 268–270 | P03 | Negative stock | 15 | Set `stock_quantity` to uniform(-200, -1) |
| 272–274 | P04 | NULL category | 20 | Set `category = None` |
| 276–279 | P05 | Invalid price | 20 | Cast price column to object, set `"INVALID"` |
| 281–284 | P06 | Cost > price | 15 | Set `cost = price + uniform(1, 50)` |

**Post-injection row count:** 1,000 + 15 = **1,016**

### 6.10 `inject_order_issues(orders, valid_customer_ids, valid_product_ids, rng)` (Lines 289–349)

Operates **in place** on the orders DataFrame.

| Lines | Code | Defect | Count | Mechanism |
|---|---|---|---|---|
| 297–298 | — | Type prep | — | Cast `customer_id` and `product_id` to `object` for mixed types |
| 301–302 | — | Orphan ID ranges | — | `max_id + 10,000` to `max_id + 10,050` (customers), `+10,000` to `+10,030` (products) |
| 304–306 | O01 | NULL customer_id | 100 | Set `customer_id = None` |
| 308–310 | O02 | NULL product_id | 200 | Set `product_id = None` |
| 312–314 | O03 | Orphan customer_id | 50 | Assign IDs from `invalid_customer_ids` range |
| 316–318 | O04 | Orphan product_id | 30 | Assign IDs from `invalid_product_ids` range |
| 320–323 | O05 | Duplicate order_id | 20 | Copy `order_id` from source index to target index |
| 325–330 | O06 | Amount mismatch | 15 | Set `total_amount = qty × price + 999.99` |
| 332–336 | O07 | Payment before order | 10 | Set `payment_date = order_date - 3 days` |
| 338–340 | O08 | Invalid status | 10 | Set `order_status = "UNKNOWN"` |
| 342–345 | O09 | Non-numeric quantity | 20 | Cast quantity to object, set `"N/A"` |
| 347–349 | O10 | Future order_date | 10 | Set `order_date = date(2027, 6, 1)` |

**Post-injection row count:** **50,000** (no rows appended; defects modify existing rows)

### 6.11 `write_csv(df, path)` (Lines 352–357)

Applies `_blank()` to every column, then writes CSV with `index=False`. Empty cells represent NULL values for Spark CSV reader.

### 6.12 `summarize_issues()` (Lines 360–372)

Converts `ISSUE_MANIFEST` to a Pandas DataFrame for console reporting.

### 6.13 `main()` (Lines 375–412)

Execution pipeline:

```
1. Seed all RNGs (L377-381)
2. Create data/ directory (L383)
3. generate_customers() → inject_customer_issues() (L385-388)
4. generate_products() → inject_product_issues() (L386-389)
5. generate_orders() → inject_order_issues() (L390-397)
6. write_csv() for all three files (L399-401)
7. Print row counts and manifest table (L403-412)
```

---

## 7. Output Files

| File | Rows | Size | Path |
|---|---|---|---|
| `customers.csv` | 10,011 | ~781 KB | `data/customers.csv` |
| `products.csv` | 1,016 | ~64 KB | `data/products.csv` |
| `orders.csv` | 50,000 | ~3.0 MB | `data/orders.csv` |

---

## 8. Defect-to-Silver-Rule Mapping

| Defect Codes | Silver Module | Error Tags |
|---|---|---|
| O01, O02 | Completeness | `NULL_CUSTOMER_ID`, `NULL_PRODUCT_ID` |
| O05 | Uniqueness | `DUPLICATE_ORDER_ID` |
| O03, O04 | Referential Integrity | `INVALID_CUSTOMER_ID_FK`, `INVALID_PRODUCT_ID_FK` |
| O07 | Business Logic | `PAYMENT_BEFORE_ORDER_DATE` |
| C01–C07, P01–P06, O06, O08–O10 | *(not yet in silver pipeline)* | Future rules |

---

## 9. Running the Generator

```bash
# From repository root
python src/data_generation/generate_sample_data.py
```

Expected stdout:

```
Sample data generation complete.
  customers.csv : 10,011 rows -> .../data/customers.csv
  products.csv  : 1,016 rows -> .../data/products.csv
  orders.csv    : 50,000 rows -> .../data/orders.csv
  intentional quality issues injected: 700

 code      table    count                              description
  C01  customers       50                              NULL email
  ...
```

---

## 10. Design Decisions

| Decision | Rationale |
|---|---|
| Inject after baseline generation | Ensures valid FK references exist before orphan injection |
| Separate orphan ID ranges (+10,000) | Guarantees no collision with valid IDs |
| `pd.concat` for duplicates | Appends extra rows (inflates count) mimicking real duplicate uploads |
| `object` dtype before mixed-type injection | Allows NULL and string values in INT columns |
| Empty CSV cells for NULL | Spark `inferSchema` reads as null, not string `"null"` |
| 50K orders (not 100K) | Balances CE serverless execution time with realistic volume |
| Supplemental 240 defects | Exercises future silver rules beyond spec minimum |

---

## 11. Verification Checklist

- [ ] `sum(ISSUE_MANIFEST counts) == 700`
- [ ] `customers.csv` has 10,011 rows (10,000 + 10 dupes)
- [ ] `products.csv` has 1,016 rows (1,000 + 15 dupes)
- [ ] `orders.csv` has exactly 50,000 rows
- [ ] Re-running with seed 42 produces identical file hashes
- [ ] Bronze ingest preserves all rows including defects
- [ ] Silver quarantines > 400 order rows
