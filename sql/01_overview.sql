-- Q1: How big is the dataset and what period does it cover?
SELECT
    COUNT(*)                         AS total_complaints,
    COUNT(DISTINCT company)          AS companies,
    COUNT(DISTINCT product)          AS products,
    MIN(date_received)               AS first_date,
    MAX(date_received)               AS last_date,
    ROUND(100.0 * AVG(timely_flag), 1) AS timely_response_pct,
    ROUND(100.0 * AVG(relief_flag), 2) AS monetary_relief_pct
FROM complaints;
