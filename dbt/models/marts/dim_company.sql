-- One row per company that appears in the complaint data.
select
    to_hex(md5(company)) as company_key,
    company as company_name
from (select distinct company from {{ ref('stg_complaints') }} where company is not null)
