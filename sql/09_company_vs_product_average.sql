-- Q9: Fair comparison. Each company is compared with the AVERAGE OF ITS OWN PRODUCT,
-- so product mix does not distort the ranking.
-- Gap columns are in percentage points (positive relief gap = more relief than average).
WITH product_avg AS (
    SELECT product,
           100.0 * AVG(timely_flag) AS prod_timely,
           100.0 * AVG(relief_flag) AS prod_relief
    FROM complaints
    GROUP BY product
),
company_product AS (
    SELECT product, company,
           COUNT(*)                 AS complaints,
           100.0 * AVG(timely_flag) AS timely,
           100.0 * AVG(relief_flag) AS relief
    FROM complaints
    WHERE product IN ('Credit card', 'Checking or savings account', 'Mortgage',
                      'Vehicle loan or lease', 'Student loan', 'Prepaid card')
    GROUP BY product, company
    HAVING COUNT(*) >= 1000
)
SELECT
    c.product,
    c.company,
    c.complaints,
    ROUND(c.timely, 1)               AS timely_pct,
    ROUND(p.prod_timely, 1)          AS product_timely_pct,
    ROUND(c.timely - p.prod_timely, 1) AS timely_gap_pts,
    ROUND(c.relief, 2)               AS relief_pct,
    ROUND(p.prod_relief, 2)          AS product_relief_pct,
    ROUND(c.relief - p.prod_relief, 2) AS relief_gap_pts
FROM company_product c
JOIN product_avg p USING (product)
ORDER BY c.product, c.complaints DESC;