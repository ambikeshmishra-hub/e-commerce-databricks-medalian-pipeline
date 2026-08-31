# E-Commerce Pipeline Technical Specification

## Datasets
1. customers.csv: customer_id (INT), customer_name (STRING), email (STRING), country (STRING), signup_date (DATE), customer_segment (STRING), lifetime_value (DECIMAL)
2. orders.csv: order_id (INT), customer_id (INT), order_date (DATE), product_id (INT), quantity (INT), unit_price (DECIMAL), total_amount (DECIMAL), order_status (STRING), payment_date (DATE)
3. products.csv: product_id (INT), product_name (STRING), category (STRING), price (DECIMAL), cost (DECIMAL), stock_quantity (INT), reorder_level (INT)

## Data Quality Requirements (~700 intentional issue rows)
- Customers: 50 NULL emails, 10 duplicate customer_ids.
- Orders: 100 NULL customer_ids, 200 NULL product_ids, 50 invalid customer_ids (FK missing), 30 invalid product_ids (FK missing), 20 duplicate order_ids.