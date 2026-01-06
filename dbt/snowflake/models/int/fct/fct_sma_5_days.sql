{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
with close_data as (select trading_date, ticker, close from {{ ref('stg_stock_data') }})
    select
        trading_date,
        ticker,
        close,
        avg(close) over (partition by ticker order by trading_date rows between 4 preceding and current row) as sma,
        last_value(close) over (partition by ticker order by trading_date rows between unbounded preceding and 1 preceding) as last_close
    from close_data