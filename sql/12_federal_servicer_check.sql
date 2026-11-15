-- Q12: What is 'SERVICER UNDER CONTRACT WITH FEDERAL STUDENT AID'?
-- All of its complaints are marked late (0% timely). Look at how they were closed
-- to judge whether this is a real service problem or a data-coding artifact.
SELECT
    company_response,
    timely_response,
    COUNT(*)            AS complaints,
    MIN(date_received)  AS first_date,
    MAX(date_received)  AS last_date
FROM complaints
WHERE company LIKE 'SERVICER UNDER CONTRACT%'
GROUP BY company_response, timely_response
ORDER BY complaints DESC;