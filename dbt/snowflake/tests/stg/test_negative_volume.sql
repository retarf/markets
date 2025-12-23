select *
from {{ ref('stg_stock_data') }}
where volume < 0