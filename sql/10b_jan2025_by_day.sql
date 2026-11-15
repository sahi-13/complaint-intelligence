-- Q10b: Was the January 2025 spike spread over the month or concentrated on a few days?
SELECT
    date_received,
    COUNT(*) AS complaints
FROM complaints
WHERE year_month = '2025-01'
GROUP BY date_received
ORDER BY complaints DESC
LIMIT 10;