-- Fails (returns a row) unless staging holds exactly the 96,155 complaints in the CFPB file
-- (the count matches the CFPB website for these filters; see data/README.md).
select count(*) as row_count
from {{ ref('stg_complaints') }}
having count(*) != 96155
