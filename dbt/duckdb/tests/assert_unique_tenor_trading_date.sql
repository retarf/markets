-- Fails if any (Tenor, Trading Date) appears more than once in the curve fact.
select
    tenor,
    trading_date,
    count(*) as n
from {{ ref('fct_yield_curve') }}
group by tenor, trading_date
having count(*) > 1
