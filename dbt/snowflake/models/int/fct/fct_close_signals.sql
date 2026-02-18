{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
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
        trading_date as close_date,
        ticker, 
        trend,
        segment
    from ranked
    where rn = 1
