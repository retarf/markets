select distinct
    ticker
    from {{ ref('stg_stock_data') }}