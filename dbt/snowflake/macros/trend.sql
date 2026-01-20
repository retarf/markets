{% macro trend(sma_column_name, last_sma_column_name) %}
case
        when close - {{ sma_column_name }} < 0 then 'down'
        when close - {{ sma_column_name }} > 0 then 'up'
end
{% endmacro %}

