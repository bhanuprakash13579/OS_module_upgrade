import os
from jinja2 import Template

template_string = """
{% if not only_page or only_page == 1 %}
PAGE 1 CONTENT
{% endif %}

{% if not only_page or only_page == 2 %}
PAGE 2 CONTENT
{% endif %}
"""

template = Template(template_string)

print("--- DEFAULT (NO KWARG) ---")
print(template.render())

print("--- PAGE 1 ---")
print(template.render(only_page=1))

print("--- PAGE 2 ---")
print(template.render(only_page=2))
