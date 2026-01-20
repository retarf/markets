{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
with sma_values as (select * from {{ ref('fct_sma') }}),
     small_signal_values as (select ticker,
                                    trading_date,
                                    {{ signal('sma_5', 'last_sma_5') }}   as signal_sma_5,
                                    {{ signal('sma_10', 'last_sma_10') }} as signal_sma_10,
                                    {{ signal('sma_20', 'last_sma_20') }} as signal_sma_20
                             from sma_values),
     signal_values as (select *, {{ all(['signal_sma_5', 'signal_sma_10', 'signal_sma_20']) }} as signal
                       from small_signal_values)
    select * from signal_values where coalesce(signal_sma_5, signal_sma_10, signal_sma_20, signal) is not null
