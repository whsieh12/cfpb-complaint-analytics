-- One row per calendar day between the first and last complaint received.
with bounds as (
    select min(received_date) as start_date, max(received_date) as end_date
    from {{ ref('stg_complaints') }}
)
select
    d as date_day,
    date_trunc(d, month) as month_start,
    extract(year from d) as year,
    extract(month from d) as month_number,
    format_date('%b %Y', d) as month_label,
    format_date('%A', d) as day_name,
    extract(dayofweek from d) in (1, 7) as is_weekend
from bounds, unnest(generate_date_array(start_date, end_date)) as d
