-- Gold mart: revenue aggregated by customer (PASS orders only)
CREATE OR REPLACE TABLE workspace.gold.gold_revenue_by_customer AS
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS total_revenue,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(AVG(c.lifetime_value), 2) AS lifetime_value_actual
FROM workspace.silver.silver_orders AS o
INNER JOIN workspace.bronze.bronze_customers AS c
    ON o.customer_id = c.customer_id
WHERE o.quality_check_result = 'PASS'
GROUP BY
    c.customer_id,
    c.customer_name,
    c.customer_segment;
