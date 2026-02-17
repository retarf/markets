{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}

with trend as (select * from {{ ref('mart_trend_data') }} order by (ticker, trading_date)),
    select * from trend
