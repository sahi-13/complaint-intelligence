-- Q6: Case study template. Change the company name in the WHERE clause.
-- Compares one company with the industry for each product.
WITH industry AS (
    SELECT product,
           ROUND(100.0 * AVG(timely_flag), 1) AS industry_timely_pct,
           ROUND(100.0 * AVG(relief_flag), 2) AS industry_relief_pct
    FROM complaints
    GROUP BY product
),
firm AS (
    SELECT product,
           COUNT(*) AS complaints,
           ROUND(100.0 * AVG(timely_flag), 1) AS timely_pct,
           ROUND(100.0 * AVG(relief_flag), 2) AS relief_pct
    FROM complaints
    WHERE company LIKE '%CITIBANK%'          -- <- change this to any company
    GROUP BY product
)
SELECT f.product, f.complaints,
       f.timely_pct, i.industry_timely_pct,
       f.relief_pct, i.industry_relief_pct
FROM firm f
JOIN industry i USING (product)
ORDER BY f.complaints DESC;
