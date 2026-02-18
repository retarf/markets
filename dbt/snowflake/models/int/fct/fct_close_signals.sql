{{ config(
    materialized='incremental',
    unique_key=['ticker', 'segment'],
    incremental_strategy='merge'
) }}

with segment_data as (select * from {{ ref('fct_trend_segments')}} where trend is not null),
    ranked as (
        select 
            *,
            row_number() over (
                partition by ticker, segment
                order by trading_date desc
            ) as rn
        from segment_data
    )
    select 
        r.trading_date as close_date,
        r.ticker, 
        trend,
        segment,
        p.close as close_price
    from ranked r
    join {{ ref('fct_close_prices') }} p
    on r.trading_date = p.trading_date
    and r.ticker = p.ticker
    where rn = 1
