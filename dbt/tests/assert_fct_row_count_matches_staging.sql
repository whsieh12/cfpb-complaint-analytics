-- The fact table must keep every complaint: returns a row if counts differ.
select s.n as staging_rows, f.n as fact_rows
from (select count(*) as n from {{ ref('stg_complaints') }}) s,
     (select count(*) as n from {{ ref('fct_complaints') }}) f
where s.n != f.n
