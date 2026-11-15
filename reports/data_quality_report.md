# Data Quality Report

- Raw rows: 1,182,415
- Dropped (missing key fields): 0
- Dropped (duplicate complaint_id): 0
- Clean rows: 1,182,415
- Date range: 2025-01-01 to 2026-11-05
- Distinct companies: 4,601
- Distinct products: 10

## Missing values (% of rows)

| Column | Missing % |
|---|---|
| narrative | 100.0 |
| tags | 89.3 |
| company_public_response | 68.8 |
| sub_issue | 13.0 |
| state | 0.5 |
| zip_code | 0.2 |
| sub_product | 0.0 |
| issue | 0.0 |
| date_received | 0.0 |
| product | 0.0 |
| submitted_via | 0.0 |
| date_sent_to_company | 0.0 |
| company_response | 0.0 |
| company | 0.0 |
| timely_response | 0.0 |
| complaint_id | 0.0 |
| year_month | 0.0 |
| year | 0.0 |
| timely_flag | 0.0 |
| relief_flag | 0.0 |
| has_narrative | 0.0 |
| days_to_company | 0.0 |

## Notes
- Narratives were removed before analysis to keep the file small, so they show as missing.
- Company names were uppercased to group variants together.