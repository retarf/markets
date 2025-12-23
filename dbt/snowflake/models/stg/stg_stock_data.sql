{{ config(
    materialized='incremental',
    unique_key=['ticker', 'trading_date'],
    incremental_strategy='merge'
) }}
with
    src as (select * from {{ source('raw', 'raw_stock_data') }}
        {%  if is_incremental() %}
            where load_ts > (select coalesce(max(load_ts), '1900-01-01'::timestamp_ntz) from {{ this }})
        {% endif %}
    ),
    dedup as (
        select
            ticker,
            trading_date,
            open,
            high,
            low,
            close,
            volume,
            source_file,
            load_ts
        from src
        qualify row_number() over (partition by ticker, trading_date order by load_ts desc, source_file desc) = 1
    )

select * from dedup