{{ config(materialized='table') }}

-- Tidy yield fact: one row per (Trading Date, Tenor) with a maturity rank so
-- consumers can order the curve by maturity. Serves both the curve snapshot
-- (filter a Trading Date) and the per-Tenor series (filter a Tenor over a window).
select
    trading_date,
    tenor,
    case tenor
        when '1M'  then 0
        when '3M'  then 1
        when '6M'  then 2
        when '1Y'  then 3
        when '2Y'  then 4
        when '3Y'  then 5
        when '5Y'  then 6
        when '7Y'  then 7
        when '10Y' then 8
        when '20Y' then 9
        when '30Y' then 10
    end as tenor_order,
    yield
from {{ ref('stg_treasury_yields') }}
