{%  macro in_list(values) -%}
    {%- for value in values -%}
        '{{ value }}'{% if not loop.last %},{% endif %}
    {%- endfor -%}
{%- endmacro %}

{% macro all(values) %}
case
    when
        {% for value in values %}
            {{ value }} = {{ values[0] }}
            {% if not loop.last %} and {% endif %}
        {% endfor %}
    then {{ values[0] }}
    else null
end
{% endmacro %}
