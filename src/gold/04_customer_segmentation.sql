-- Gold mart: customer segmentation by order behavior (PASS orders only)
CREATE OR REPLACE TABLE workspace.gold.gold_customer_segmentation AS
WITH customer_orders AS (
    SELECT
        o.customer_id,
        COUNT(o.order_id) AS total_orders,
        ROUND(SUM(o.total_amount), 2) AS total_revenue
    FROM workspace.silver.silver_orders AS o
    WHERE o.quality_check_result = 'PASS'
    GROUP BY
        o.customer_id
),
segmented_customers AS (
    SELECT
        co.customer_id,
        co.total_orders,
        co.total_revenue,
        CASE
            WHEN co.total_revenue > 3000 THEN 'High-Value'
            WHEN co.total_orders > 5 THEN 'Repeat'
            WHEN co.total_orders = 1 THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type
    FROM customer_orders AS co
)
SELECT
    sc.segment_type,
    COUNT(DISTINCT sc.customer_id) AS customer_count,
    ROUND(AVG(sc.total_revenue), 2) AS avg_revenue,
    ROUND(SUM(sc.total_revenue), 2) AS total_revenue
FROM segmented_customers AS sc
GROUP BY
    sc.segment_type;
