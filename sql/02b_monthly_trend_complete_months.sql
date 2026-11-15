-- Q2b: Monthly trend, leaving out the latest (incomplete) month.
-- The newest month is partial and recent complaints are still being added,
-- so it would wrongly look like a drop in volume.
WITH monthly AS (
    SELECT year_month, COUNT(*) AS complaints
    FROM complaints
    GROUP BY year_month
),
complete_months AS (
    SELECT * FROM monthly
    WHERE year_month < (SELECT MAX(year_month) FROM monthly)
)
SELECT
    year_month,
    complaints,
    LAG(complaints) OVER (ORDER BY year_month) AS prev_month,
    ROUND(100.0 * (complaints - LAG(complaints) OVER (ORDER BY year_month))
          / LAG(complaints) OVER (ORDER BY year_month), 1) AS mom_growth_pct
FROM complete_months
ORDER BY year_month;