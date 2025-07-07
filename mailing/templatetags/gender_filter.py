from django import template

register = template.Library()

@register.filter
def gender_format(value: str, gender: str) -> str:
    """
    Replaces placeholders like 'żądałeś|żądałaś' based on gender.
    'm' = masculine, 'f' = feminine
    """
    import re

    def replace(match):
        masculine, feminine = match.group(1).split('|')
        return feminine if gender == 'K' else masculine

    return re.sub(r'(\w+\|\w+)', replace, value)