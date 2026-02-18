{{ config(
    materialized='incremental',
    unique_key=['ticker', 'segment'],
    incremental_strategy='merge'
) }}

with open_signals as (select * from {{ ref('fct_open_signals') }}),
    close_signals as (select * from {{ ref('fct_close_signals') }})
    select
        o.ticker,
        o.trend,
        open_date,
        open_price,
        close_date,
        close_price,
        case
            when o.trend = 'up' then close_price - open_price 
            when o.trend = 'down' then open_price - close_price 
        end as profit_per_share,
        case
            when o.trend = 'up' then (close_price - open_price) / open_price * 100
            when o.trend = 'down' then (open_price - close_price) / open_price * 100
        end as return_rate,
        o.segment
    from close_signals c
    join open_signals o
    on o.ticker = c.ticker
    and o.segment = c.segment