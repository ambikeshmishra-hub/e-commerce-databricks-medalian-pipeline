-- =============================================================================
-- Tile 1 Query (Horizontal Bar Chart): Top 10 Products by Revenue
-- Visual intent: Highlight the highest-earning products to guide inventory and
--                 merchandising decisions in a ranked horizontal bar chart.
-- =============================================================================
SELECT
    product_name,
    category,
    total_revenue
FROM workspace.gold.gold_sales_by_product
ORDER BY
    total_revenue DESC
LIMIT 10;

-- =============================================================================
-- Tile 2 Query (Histogram / Column Chart): Customer Revenue Distribution
-- Visual intent: Show how customers are spread across revenue tiers to expose
--                 concentration and long-tail purchasing behavior.
-- =============================================================================
SELECT
    CASE
        WHEN total_revenue <= 500 THEN '0 - 500'
        WHEN total_revenue <= 1500 THEN '500 - 1500'
        WHEN total_revenue <= 3000 THEN '1501 - 3000'
        ELSE '3000+'
    END AS revenue_bucket,
    COUNT(*) AS customer_count
FROM workspace.gold.gold_revenue_by_customer
GROUP BY
    CASE
        WHEN total_revenue <= 500 THEN '0 - 500'
        WHEN total_revenue <= 1500 THEN '500 - 1500'
        WHEN total_revenue <= 3000 THEN '1501 - 3000'
        ELSE '3000+'
    END
ORDER BY
    CASE revenue_bucket
        WHEN '0 - 500' THEN 1
        WHEN '500 - 1500' THEN 2
        WHEN '1501 - 3000' THEN 3
        WHEN '3000+' THEN 4
    END;

-- =============================================================================
-- Tile 3 Query (Pie / Donut Chart): Customer Segmentation Breakdown
-- Visual intent: Compare segment share by customer count and revenue contribution
--                 for strategic marketing and retention planning.
-- =============================================================================
SELECT
    segment_type,
    customer_count,
    total_revenue
FROM workspace.gold.gold_customer_segmentation
ORDER BY
    CASE segment_type
        WHEN 'High-Value' THEN 1
        WHEN 'Repeat' THEN 2
        WHEN 'One-Time' THEN 3
        WHEN 'Inactive' THEN 4
    END;
