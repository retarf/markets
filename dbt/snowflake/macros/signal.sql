{% macro signal(sma_column_name, last_sma_column_name) %}
case
        when last_close - {{ last_sma_column_name }} >= 0 and close - {{ sma_column_name }} < 0 then 'down'
        when last_close - {{ last_sma_column_name }} <= 0 and close - {{ sma_column_name }} > 0 then 'up'
        else null
end
{% endmacro %}
