-- Q5: Compare the 15 companies with the most complaints.
-- Rates are shown next to volume so a big company is not judged on counts alone.
SELECT
    company,
    COUNT(*)                               AS complaints,
    ROUND(100.0 * AVG(timely_flag), 1)     AS timely_pct,
    ROUND(100.0 * AVG(relief_flag), 2)     AS relief_pct,
    ROUND(AVG(days_to_company), 1)         AS avg_days_to_company,
    RANK() OVER (ORDER BY COUNT(*) DESC)   AS volume_rank
FROM complaints
GROUP BY company
ORDER BY complaints DESC
LIMIT 15;
