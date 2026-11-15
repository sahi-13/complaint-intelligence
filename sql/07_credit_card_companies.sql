-- Q7: Top 10 companies by CREDIT CARD complaints.
-- HAVING keeps only companies with enough complaints for the rates to be reliable.
SELECT
    company,
    COUNT(*)                              AS complaints,
    ROUND(100.0 * AVG(timely_flag), 1)    AS timely_pct,
    ROUND(100.0 * AVG(relief_flag), 2)    AS relief_pct,
    ROUND(AVG(days_to_company), 1)        AS avg_days_to_company
FROM complaints
WHERE product = 'Credit card'
GROUP BY company
HAVING COUNT(*) >= 1000
ORDER BY complaints DESC
LIMIT 10;