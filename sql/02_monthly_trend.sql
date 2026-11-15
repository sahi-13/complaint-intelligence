-- Q2: How does complaint volume change month to month?
-- Uses a CTE for monthly counts and LAG() for month-over-month growth.
WITH monthly AS (
    SELECT year_month, COUNT(*) AS complaints
    FROM complaints
    GROUP BY year_month
)
SELECT
    year_month,
    complaints,
    LAG(complaints) OVER (ORDER BY year_month) AS prev_month,
    ROUND(100.0 * (complaints - LAG(complaints) OVER (ORDER BY year_month))
          / LAG(complaints) OVER (ORDER BY year_month), 1) AS mom_growth_pct
FROM monthly
ORDER BY year_month;
