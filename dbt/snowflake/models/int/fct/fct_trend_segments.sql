{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}

with trend_data as (select * from {{ ref('fct_trend')}}),
    trend_data_with_prev_trend as (select *, lag(trend) over (partition by ticker order by trading_date) as prev_trend from trend_data),
    trend_data_with_new_trend as (
        select *, 
            case
                when trend is not null and not equal_null(trend, prev_trend) then 1 else 0
            end as is_new_trend
        from trend_data_with_prev_trend
    )
    select 
        *, 
        sum(case when trend is not null then is_new_trend else 0 end) over (
            partition by ticker 
            order by trading_date
            rows between unbounded preceding and current row
        ) as segment 
    from trend_data_with_new_trend
    
