-- Q4: Top 3 issues inside each product (window function: RANK per partition).
WITH issue_counts AS (
    SELECT product, issue, COUNT(*) AS complaints
    FROM complaints
    GROUP BY product, issue
),
ranked AS (
    SELECT
        product, issue, complaints,
        RANK() OVER (PARTITION BY product ORDER BY complaints DESC) AS rnk
    FROM issue_counts
)
SELECT product, rnk, issue, complaints
FROM ranked
WHERE rnk <= 3
ORDER BY product, rnk;
