-- One row per issue / sub-issue combination.
select
    to_hex(md5(concat(issue, '|', coalesce(sub_issue, '')))) as issue_key,
    issue,
    sub_issue
from (
    select distinct issue, sub_issue
    from {{ ref('stg_complaints') }}
    where issue is not null
)
