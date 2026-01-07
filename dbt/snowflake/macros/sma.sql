{% macro sma(column_name, num_of_periods) %}
    avg({{ column_name }}) over (partition by ticker order by trading_date rows between {{ num_of_periods - 1 }} preceding and current row)
{% endmacro %}