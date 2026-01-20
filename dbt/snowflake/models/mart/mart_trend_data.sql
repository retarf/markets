{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}

with close_prices as (select * from {{ ref('fct_close_prices') }}),
     trend as (select * from {{ ref('fct_trend') }}),
     signals as (select * from {{ ref('fct_signals') }})
    select
        cp.trading_date,
        cp.ticker,
        close,
        trend_sma_5,
        trend_sma_10,
        trend_sma_20,
        trend,
        signal_sma_5,
        signal_sma_10,
        signal_sma_20,
        signal
    from close_prices as cp
    left join trend as t on t.trading_date = cp.trading_date and t.ticker = cp.ticker
    left join signals as s on s.trading_date = cp.trading_date and s.ticker = cp.ticker
