{% macro trend(sma_column_name, last_sma_column_name) %}
        case
                when close - {{ sma_column_name }} < 0 then 'down'
                when close - {{ sma_column_name }} > 0 then 'up'
        end
{% endmacro %}


{% macro get_trend_id(ticker, trading_date) %}
        concat({{ ticker}}, '-', to_char({{ trading_date }}, 'YYYYMMDD'))
{% endmacro %}