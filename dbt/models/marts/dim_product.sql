-- One row per product / sub-product combination.
select
    to_hex(md5(concat(product, '|', coalesce(sub_product, '')))) as product_key,
    product,
    sub_product
from (
    select distinct product, sub_product
    from {{ ref('stg_complaints') }}
    where product is not null
)
