-- Q11: Credit card benchmark WITHOUT the three credit bureaus.
-- The bureaus appear under 'Credit card' with ~0% relief, which pulls the product average down.
-- The product average is recomputed here without them.
WITH cc AS (
    SELECT *
    FROM complaints
    WHERE product = 'Credit card'
      AND company NOT LIKE '%EQUIFAX%'
      AND company NOT LIKE '%TRANSUNION%'
      AND company NOT LIKE '%EXPERIAN%'
),
avg_all AS (
    SELECT ROUND(100.0 * AVG(relief_flag), 2) AS prod_relief,
           ROUND(100.0 * AVG(timely_flag), 1) AS prod_timely,
           COUNT(*) AS prod_complaints
    FROM cc
)
SELECT
    c.company,
    COUNT(*)                                   AS complaints,
    ROUND(100.0 * AVG(c.timely_flag), 1)       AS timely_pct,
    ROUND(100.0 * AVG(c.relief_flag), 2)       AS relief_pct,
    a.prod_relief                              AS product_relief_pct_ex_bureaus,
    ROUND(100.0 * AVG(c.relief_flag) - a.prod_relief, 2) AS relief_gap_pts
FROM cc c
CROSS JOIN avg_all a
GROUP BY c.company, a.prod_relief
HAVING COUNT(*) >= 1000
ORDER BY complaints DESC
LIMIT 15;