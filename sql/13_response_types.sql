-- Q13: How do companies close complaints? Shows every response category and its share.
-- 'relief_flag' only counts 'Closed with monetary relief', so we need to know what the
-- other categories are before deciding whether the relief metric is fair across companies.
SELECT
    company_response,
    COUNT(*) AS complaints,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM complaints
GROUP BY company_response
ORDER BY complaints DESC;