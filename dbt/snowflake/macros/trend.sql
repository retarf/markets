{% macro trend(sma_column_name, last_sma_column_name) %}
    case
        when last_close - {{ last_sma_column_name }} >= 0 and close - {{ sma_column_name }} < 0 then 'signal_down'
        when last_close - {{ last_sma_column_name }} <= 0 and close - {{ sma_column_name }} > 0 then 'signal_up'
        when close - {{ sma_column_name }} < 0 then 'trend_down'
        when close - {{ sma_column_name }} > 0 then 'trend_up'
    end
{% endmacro %}
