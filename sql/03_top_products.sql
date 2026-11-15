-- Q3: Which products generate the most complaints, and what share is that?
SELECT
    product,
    COUNT(*) AS complaints,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct,
    ROUND(100.0 * AVG(timely_flag), 1)  AS timely_pct,
    ROUND(100.0 * AVG(relief_flag), 2)  AS relief_pct
FROM complaints
GROUP BY product
ORDER BY complaints DESC;
