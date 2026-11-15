-- Q10: What caused the January 2025 spike (about 110k complaints vs 41-45k in the next months)?
-- Looks at which product + company pairs account for it.
SELECT
    product,
    company,
    COUNT(*) AS complaints,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_month_pct
FROM complaints
WHERE year_month = '2025-01'
GROUP BY product, company
ORDER BY complaints DESC
LIMIT 10;