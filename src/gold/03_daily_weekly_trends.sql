-- Gold mart: daily and weekly order trends (PASS orders only)
CREATE OR REPLACE TABLE workspace.gold.gold_daily_weekly_trends AS
SELECT
    CAST(o.order_date AS DATE) AS order_date,
    DATE_TRUNC('week', CAST(o.order_date AS DATE)) AS order_week,
    COUNT(o.order_id) AS daily_order_count,
    ROUND(SUM(o.total_amount), 2) AS daily_revenue
FROM workspace.silver.silver_orders AS o
WHERE o.quality_check_result = 'PASS'
GROUP BY
    CAST(o.order_date AS DATE),
    DATE_TRUNC('week', CAST(o.order_date AS DATE))
ORDER BY
    order_date ASC;
