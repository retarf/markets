{{ config(materialized='ephemeral') }}

-- Typed, deduplicated one-row-per-(Tenor, Trading Date) view of the raw yields.
-- Gaps are preserved: rows the Treasury never printed simply do not exist here.
with src as (
    select
        tenor,
        trading_date,
        yield,
        load_ts
    from {{ source('raw', 'raw_treasury_yields') }}
)
select
    tenor,
    trading_date,
    yield
from src
qualify row_number() over (
    partition by tenor, trading_date order by load_ts desc
) = 1
