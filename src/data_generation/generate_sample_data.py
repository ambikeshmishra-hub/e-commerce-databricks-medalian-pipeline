"""Generate e-commerce sample CSVs with intentional data-quality defects.

Creates customers.csv, orders.csv, and products.csv under data/ using Faker,
NumPy, and Pandas. Injects exactly 700 tracked quality issues aligned with
tool-specific/cursor-workflow/spec.md and silver-layer validation categories.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
NUM_CUSTOMERS = 10_000
NUM_PRODUCTS = 1_000
NUM_ORDERS = 50_000

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Shipped", "Delivered", "Cancelled", "Returned")
PRODUCT_CATEGORIES = (
    "Electronics",
    "Clothing",
    "Home",
    "Sports",
    "Books",
    "Beauty",
    "Toys",
)

SEGMENT_LTV_RANGES = {
    "Premium": (500.0, 15_000.0),
    "Standard": (100.0, 3_000.0),
    "Basic": (0.0, 800.0),
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

SIGNUP_START = date(2020, 1, 1)
SIGNUP_END = date(2024, 12, 31)
ORDER_END = date(2025, 12, 31)


@dataclass(frozen=True)
class IssueSpec:
    """Single intentional defect category."""

    code: str
    table: str
    count: int
    description: str


# Spec-required (460) + supplemental silver-layer defects (240) = 700 total.
ISSUE_MANIFEST: tuple[IssueSpec, ...] = (
    # --- customers.csv (spec) ---
    IssueSpec("C01", "customers", 50, "NULL email"),
    IssueSpec("C02", "customers", 10, "duplicate customer_id"),
    # --- orders.csv (spec) ---
    IssueSpec("O01", "orders", 100, "NULL customer_id"),
    IssueSpec("O02", "orders", 200, "NULL product_id"),
    IssueSpec("O03", "orders", 50, "invalid customer_id (missing FK)"),
    IssueSpec("O04", "orders", 30, "invalid product_id (missing FK)"),
    IssueSpec("O05", "orders", 20, "duplicate order_id"),
    # --- customers.csv (supplemental) ---
    IssueSpec("C03", "customers", 15, "NULL customer_name"),
    IssueSpec("C04", "customers", 15, "invalid email format"),
    IssueSpec("C05", "customers", 10, "future signup_date"),
    IssueSpec("C06", "customers", 15, "invalid customer_segment"),
    IssueSpec("C07", "customers", 15, "negative lifetime_value"),
    # --- products.csv (supplemental) ---
    IssueSpec("P01", "products", 20, "NULL product_name"),
    IssueSpec("P02", "products", 15, "duplicate product_id"),
    IssueSpec("P03", "products", 15, "negative stock_quantity"),
    IssueSpec("P04", "products", 20, "NULL category"),
    IssueSpec("P05", "products", 20, "invalid price (non-numeric)"),
    IssueSpec("P06", "products", 15, "cost greater than price"),
    # --- orders.csv (supplemental) ---
    IssueSpec("O06", "orders", 15, "total_amount != quantity * unit_price"),
    IssueSpec("O07", "orders", 10, "payment_date before order_date"),
    IssueSpec("O08", "orders", 10, "invalid order_status"),
    IssueSpec("O09", "orders", 20, "invalid quantity (non-numeric)"),
    IssueSpec("O10", "orders", 10, "future order_date"),
)


def _rng() -> np.random.Generator:
    return np.random.default_rng(RANDOM_SEED)


def _pick_indices(pool_size: int, count: int, rng: np.random.Generator) -> List[int]:
    if count > pool_size:
        raise ValueError(f"Cannot pick {count} unique indices from pool of {pool_size}.")
    return sorted(rng.choice(pool_size, size=count, replace=False).tolist())


def _blank(value: object) -> str:
    """Render NULL-like values as empty CSV cells."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    return str(value)


def _random_date(rng: np.random.Generator, start: date, end: date) -> date:
    delta_days = (end - start).days
    offset = int(rng.integers(0, delta_days + 1))
    return start + timedelta(days=offset)


def generate_customers(fake: Faker, rng: np.random.Generator) -> pd.DataFrame:
    """Build the customers dimension with realistic baseline values."""
    customer_ids = np.arange(1, NUM_CUSTOMERS + 1)
    segments = rng.choice(list(CUSTOMER_SEGMENTS), size=NUM_CUSTOMERS, p=[0.2, 0.5, 0.3])

    rows: list[dict[str, object]] = []
    for idx, customer_id in enumerate(customer_ids):
        segment = segments[idx]
        low, high = SEGMENT_LTV_RANGES[segment]
        signup_date = _random_date(rng, SIGNUP_START, SIGNUP_END)
        rows.append(
            {
                "customer_id": int(customer_id),
                "customer_name": fake.name(),
                "email": fake.unique.email(),
                "country": fake.country(),
                "signup_date": signup_date,
                "customer_segment": segment,
                "lifetime_value": round(float(rng.uniform(low, high)), 2),
            }
        )

    return pd.DataFrame(rows)


def generate_products(rng: np.random.Generator) -> pd.DataFrame:
    """Build the products catalog with realistic baseline values."""
    fake = Faker()
    Faker.seed(RANDOM_SEED + 1)

    rows: list[dict[str, object]] = []
    for product_id in range(1, NUM_PRODUCTS + 1):
        category = rng.choice(list(PRODUCT_CATEGORIES))
        price = round(float(rng.uniform(5.0, 500.0)), 2)
        cost = round(price * float(rng.uniform(0.35, 0.75)), 2)
        rows.append(
            {
                "product_id": product_id,
                "product_name": fake.catch_phrase(),
                "category": category,
                "price": price,
                "cost": cost,
                "stock_quantity": int(rng.integers(0, 500)),
                "reorder_level": int(rng.integers(10, 100)),
            }
        )

    return pd.DataFrame(rows)


def generate_orders(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Build order line items referencing valid customer and product ids."""
    customer_ids = customers["customer_id"].astype(int).tolist()
    product_catalog = products[["product_id", "price"]].copy()
    product_catalog["product_id"] = product_catalog["product_id"].astype(int)
    product_catalog["price"] = pd.to_numeric(product_catalog["price"], errors="coerce")
    product_catalog = product_catalog.dropna(subset=["price"])

    signup_lookup = customers.set_index("customer_id")["signup_date"].to_dict()

    rows: list[dict[str, object]] = []
    for order_id in range(1, NUM_ORDERS + 1):
        customer_id = int(rng.choice(customer_ids))
        product_row = product_catalog.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        product_id = int(product_row["product_id"])
        unit_price = round(float(product_row["price"]) * float(rng.uniform(0.95, 1.05)), 2)
        quantity = int(rng.integers(1, 6))

        signup_date = signup_lookup[customer_id]
        order_start = signup_date if signup_date <= ORDER_END else SIGNUP_START
        order_date = _random_date(rng, order_start, ORDER_END)
        payment_date = order_date + timedelta(days=int(rng.integers(0, 14)))

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": round(quantity * unit_price, 2),
                "order_status": rng.choice(list(ORDER_STATUSES)),
                "payment_date": payment_date,
            }
        )

    return pd.DataFrame(rows)


def inject_customer_issues(customers: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Apply customer-table defects and return the updated dataframe."""
    n = len(customers)

    null_email_idx = _pick_indices(n, 50, rng)
    for i in null_email_idx:
        customers.at[i, "email"] = None

    dup_source_idx = _pick_indices(n, 10, rng)
    duplicate_rows = customers.iloc[dup_source_idx].copy()
    customers = pd.concat([customers, duplicate_rows], ignore_index=True)

    null_name_idx = _pick_indices(n, 15, rng)
    for i in null_name_idx:
        customers.at[i, "customer_name"] = None

    bad_email_idx = _pick_indices(n, 15, rng)
    for i in bad_email_idx:
        customers.at[i, "email"] = "not-an-email"

    future_signup_idx = _pick_indices(n, 10, rng)
    for i in future_signup_idx:
        customers.at[i, "signup_date"] = date(2027, 1, 1)

    bad_segment_idx = _pick_indices(n, 15, rng)
    for i in bad_segment_idx:
        customers.at[i, "customer_segment"] = "VIP"

    negative_ltv_idx = _pick_indices(n, 15, rng)
    for i in negative_ltv_idx:
        customers.at[i, "lifetime_value"] = round(float(rng.uniform(-500.0, -1.0)), 2)

    return customers


def inject_product_issues(products: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Apply product-table defects and return the updated dataframe."""
    n = len(products)

    null_name_idx = _pick_indices(n, 20, rng)
    for i in null_name_idx:
        products.at[i, "product_name"] = None

    dup_source_idx = _pick_indices(n, 15, rng)
    duplicate_rows = products.iloc[dup_source_idx].copy()
    products = pd.concat([products, duplicate_rows], ignore_index=True)

    negative_stock_idx = _pick_indices(n, 15, rng)
    for i in negative_stock_idx:
        products.at[i, "stock_quantity"] = int(rng.integers(-200, -1))

    null_category_idx = _pick_indices(n, 20, rng)
    for i in null_category_idx:
        products.at[i, "category"] = None

    bad_price_idx = _pick_indices(n, 20, rng)
    products["price"] = products["price"].astype(object)
    for i in bad_price_idx:
        products.at[i, "price"] = "INVALID"

    cost_gt_price_idx = _pick_indices(n, 15, rng)
    for i in cost_gt_price_idx:
        price = float(products.at[i, "price"]) if isinstance(products.at[i, "price"], (int, float)) else 100.0
        products.at[i, "cost"] = round(price + float(rng.uniform(1.0, 50.0)), 2)

    return products


def inject_order_issues(
    orders: pd.DataFrame,
    valid_customer_ids: Iterable[int],
    valid_product_ids: Iterable[int],
    rng: np.random.Generator,
) -> None:
    """Apply order-table defects in place."""
    n = len(orders)
    orders["customer_id"] = orders["customer_id"].astype(object)
    orders["product_id"] = orders["product_id"].astype(object)
    max_customer_id = max(valid_customer_ids)
    max_product_id = max(valid_product_ids)
    invalid_customer_ids = list(range(max_customer_id + 10_000, max_customer_id + 10_050))
    invalid_product_ids = list(range(max_product_id + 10_000, max_product_id + 10_030))

    null_customer_idx = _pick_indices(n, 100, rng)
    for i in null_customer_idx:
        orders.at[i, "customer_id"] = None

    null_product_idx = _pick_indices(n, 200, rng)
    for i in null_product_idx:
        orders.at[i, "product_id"] = None

    invalid_customer_idx = _pick_indices(n, 50, rng)
    for offset, i in enumerate(invalid_customer_idx):
        orders.at[i, "customer_id"] = invalid_customer_ids[offset % len(invalid_customer_ids)]

    invalid_product_idx = _pick_indices(n, 30, rng)
    for offset, i in enumerate(invalid_product_idx):
        orders.at[i, "product_id"] = invalid_product_ids[offset % len(invalid_product_ids)]

    dup_source_idx = _pick_indices(n, 20, rng)
    dup_target_idx = _pick_indices(n, 20, rng)
    for src, tgt in zip(dup_source_idx, dup_target_idx):
        orders.at[tgt, "order_id"] = orders.at[src, "order_id"]

    mismatch_idx = _pick_indices(n, 15, rng)
    for i in mismatch_idx:
        quantity = orders.at[i, "quantity"]
        unit_price = orders.at[i, "unit_price"]
        if isinstance(quantity, (int, float)) and isinstance(unit_price, (int, float)):
            orders.at[i, "total_amount"] = round(float(quantity) * float(unit_price) + 999.99, 2)

    payment_before_idx = _pick_indices(n, 10, rng)
    for i in payment_before_idx:
        order_date = orders.at[i, "order_date"]
        if isinstance(order_date, date):
            orders.at[i, "payment_date"] = order_date - timedelta(days=3)

    bad_status_idx = _pick_indices(n, 10, rng)
    for i in bad_status_idx:
        orders.at[i, "order_status"] = "UNKNOWN"

    bad_quantity_idx = _pick_indices(n, 20, rng)
    orders["quantity"] = orders["quantity"].astype(object)
    for i in bad_quantity_idx:
        orders.at[i, "quantity"] = "N/A"

    future_order_idx = _pick_indices(n, 10, rng)
    for i in future_order_idx:
        orders.at[i, "order_date"] = date(2027, 6, 1)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write dataframe to CSV preserving blank NULL cells."""
    formatted = df.copy()
    for column in formatted.columns:
        formatted[column] = formatted[column].map(_blank)
    formatted.to_csv(path, index=False)


def summarize_issues() -> pd.DataFrame:
    """Return manifest as dataframe for console reporting."""
    return pd.DataFrame(
        [
            {
                "code": spec.code,
                "table": spec.table,
                "count": spec.count,
                "description": spec.description,
            }
            for spec in ISSUE_MANIFEST
        ]
    )


def main() -> None:
    """Generate datasets, inject quality defects, and write CSV outputs."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    fake = Faker()
    Faker.seed(RANDOM_SEED)
    rng = _rng()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    customers = generate_customers(fake, rng)
    products = generate_products(rng)

    customers = inject_customer_issues(customers, rng)
    products = inject_product_issues(products, rng)
    orders = generate_orders(customers, products, rng)

    inject_order_issues(
        orders,
        customers["customer_id"].astype(int).tolist(),
        products["product_id"].astype(int).tolist(),
        rng,
    )

    write_csv(customers, DATA_DIR / "customers.csv")
    write_csv(products, DATA_DIR / "products.csv")
    write_csv(orders, DATA_DIR / "orders.csv")

    manifest = summarize_issues()
    total_issues = int(manifest["count"].sum())

    print("Sample data generation complete.")
    print(f"  customers.csv : {len(customers):,} rows -> {DATA_DIR / 'customers.csv'}")
    print(f"  products.csv  : {len(products):,} rows -> {DATA_DIR / 'products.csv'}")
    print(f"  orders.csv    : {len(orders):,} rows -> {DATA_DIR / 'orders.csv'}")
    print(f"  intentional quality issues injected: {total_issues}")
    print()
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
