from django import template

register = template.Library()


@register.simple_tag
def template_exists(template_name: str):
    try:
        template.loader.get_template(template_name)
        return True
    except template.TemplateDoesNotExist:
        return False
