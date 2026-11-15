-- Q8b: Is the student-loan timeliness problem new, or has it always been there?
SELECT
    year_month,
    COUNT(*)                              AS complaints,
    ROUND(100.0 * AVG(timely_flag), 1)    AS timely_pct
FROM complaints
WHERE product = 'Student loan'
GROUP BY year_month
ORDER BY year_month;