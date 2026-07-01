{{ config(materialized='table') }}

-- The 2s10s Spread per Trading Date: 10Y minus 2Y, in basis points, derived from
-- the stored legs. A date missing either leg has no spread row (gap preserved).
with legs as (
    select
        trading_date,
        max(case when tenor = '2Y'  then yield end) as y2,
        max(case when tenor = '10Y' then yield end) as y10
    from {{ ref('stg_treasury_yields') }}
    group by trading_date
)
select
    trading_date,
    round((y10 - y2) * 100) as spread_bps,
    (y10 - y2) < 0 as is_inverted
from legs
where y2 is not null
  and y10 is not null
