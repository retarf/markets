{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
with close_data as (select trading_date, ticker, close from {{ ref('stg_stock_data') }}),
calculations as (
    select
        trading_date,
        ticker,
        close,
        {{ sma('close', 5) }} as sma_5,
    from close_data
)
select
    trading_date,
    ticker,
    close,
    sma_5,
    LAG(close) over (partition by ticker order by trading_date) as last_close,
    LAG(sma_5) over (partition by ticker order by trading_date) as last_sma_5
from calculations
