from django import template

register = template.Library()


@register.filter
def cut_text(url: str) -> str:
    url = url.split("&")
    for urll in url:
        if "producent=" in urll:
            return urll.split("producent=")[1]