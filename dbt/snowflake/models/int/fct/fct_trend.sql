{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
with sma_values as (select * from {{ ref('fct_sma') }}),
     trend_values as (
    select
        ticker,
        trading_date,
        {{ trend('sma_5', 'last_sma_5') }} as trend_sma_5,
        {{ trend('sma_10', 'last_sma_10') }} as trend_sma_10,
        {{ trend('sma_20', 'last_sma_20') }} as trend_sma_20
    from sma_values)
    select *, {{ all(['trend_sma_5', 'trend_sma_10', 'trend_sma_20']) }} as trend from trend_values
