-- Fails if any modelled Yield falls outside the sane band (a rate, not a price).
select
    tenor,
    trading_date,
    yield
from {{ ref('fct_yield_curve') }}
where yield < -5
   or yield > 25
