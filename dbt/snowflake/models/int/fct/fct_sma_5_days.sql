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
        avg(close) over (partition by ticker order by trading_date rows between 4 preceding and current row) as sma,
    from close_data
)
select
    trading_date,
    ticker,
    close,
    sma,
    LAG(close) over (partition by ticker order by trading_date) as last_close,
    LAG(sma) over (partition by ticker order by trading_date) as last_sma
from calculations
