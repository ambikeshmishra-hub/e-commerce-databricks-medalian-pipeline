-- Gold mart: sales aggregated by product (PASS orders only)
CREATE OR REPLACE TABLE workspace.gold.gold_sales_by_product AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM workspace.silver.silver_orders AS o
INNER JOIN workspace.bronze.bronze_products AS p
    ON o.product_id = p.product_id
WHERE o.quality_check_result = 'PASS'
GROUP BY
    p.product_id,
    p.product_name,
    p.category;
