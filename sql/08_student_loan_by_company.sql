-- Q8: Who drives the low student-loan timeliness (69%)?
-- Sorted by the NUMBER of late responses, since that shows who contributes most.
SELECT
    company,
    COUNT(*)                              AS complaints,
    ROUND(100.0 * AVG(timely_flag), 1)    AS timely_pct,
    SUM(1 - timely_flag)                  AS late_responses
FROM complaints
WHERE product = 'Student loan'
GROUP BY company
HAVING COUNT(*) >= 200
ORDER BY late_responses DESC
LIMIT 10;