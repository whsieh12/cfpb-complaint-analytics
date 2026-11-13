-- One row per complaint. Types the raw text columns, trims text, and adds simple outcome flags.
-- No row is dropped here: every raw row must reach this model (see tests/assert_row_count_matches_cfpb.sql).

with source as (

    select * from {{ source('raw', 'raw_complaints') }}

),

typed as (

    select
        safe_cast(nullif(trim(complaint_id), '') as int64)                  as complaint_id,
        safe_cast(nullif(trim(date_received), '') as timestamp)             as received_at,
        safe_cast(nullif(trim(date_sent_to_company), '') as timestamp)      as sent_to_company_at,
        nullif(trim(product), '')                                           as product,
        nullif(trim(sub_product), '')                                       as sub_product,
        nullif(trim(issue), '')                                             as issue,
        nullif(trim(sub_issue), '')                                         as sub_issue,
        nullif(trim(company), '')                                           as company,
        upper(nullif(trim(state), ''))                                      as state,
        nullif(trim(zip_code), '')                                          as zip_code,
        nullif(trim(tags), '')                                              as tags,
        nullif(trim(submitted_via), '')                                     as submitted_via,
        nullif(trim(company_public_response), '')                           as company_public_response,
        nullif(trim(company_response_to_consumer), '')                      as company_response_to_consumer,
        case lower(trim(timely_response))
            when 'yes' then true
            when 'no'  then false
        end                                                                 as is_timely_response
    from source

)

select
    *,
    date(received_at)                                                       as received_date,
    date_trunc(date(received_at), month)                                    as received_month,
    company_response_to_consumer = 'Closed with monetary relief'            as got_monetary_relief,
    company_response_to_consumer = 'Closed with non-monetary relief'        as got_non_monetary_relief
from typed
