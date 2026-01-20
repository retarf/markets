{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
{#with close_prices as (select trading_date, ticker, close from {{ ref('stg_stock_data') }})#}
{#    select * from close_prices#}
select trading_date, ticker, close from {{ ref('stg_stock_data') }}
