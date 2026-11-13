-- Fact table: one row per complaint, keyed to the dimensions.
select
    complaint_id,
    received_date as date_day,
    to_hex(md5(company)) as company_key,
    to_hex(md5(concat(product, '|', coalesce(sub_product, '')))) as product_key,
    to_hex(md5(concat(issue, '|', coalesce(sub_issue, '')))) as issue_key,
    state,
    submitted_via,
    company_response_to_consumer,
    is_timely_response,
    got_monetary_relief,
    got_non_monetary_relief,
    date_diff(date(sent_to_company_at), received_date, day) as days_to_reach_company
from {{ ref('stg_complaints') }}
