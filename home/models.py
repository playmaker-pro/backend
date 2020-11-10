from django.db import models

from wagtail.core.models import Page


class HomePage(Page):
    template = 'home/home.html'
    mx_count = 1

    class Meta:
        verbose_name = 'PlayMaker Main Page'
