import json

from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer


def json_filed_data_prettified(field, reverse=False, limit=5000):
    """Function to display pretty version of our data"""
    if reverse:
        field.reverse()
    response = json.dumps(field, sort_keys=True, indent=2)

    response = response[:limit]
    formatter = HtmlFormatter(style="colorful")
    response = highlight(response, JsonLexer(), formatter)
    style = "<style>" + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + response)
