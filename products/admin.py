from django.contrib import admin
from . import models 
from utils import linkify
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from django.contrib import admin
from django.utils.safestring import mark_safe
from app.utils.admin import json_filed_data_prettified


@admin.register(models.Product)
class ProductModel(admin.ModelAdmin):
    list_display = ('id', 'title', 'active', 'subtitle', 'place', 'person', 'teaser', 'slug')
    search_fields = ('tags__name',)


@admin.register(models.Request)
class RequestModel(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_display = ('id', 'user', linkify('product'), 'date')
    autocomplete_fields = ('user',)
    readonly_fields = ('data_prettified',)

    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.raw_body)


@admin.register(models.Tag)
class TagModel(admin.ModelAdmin):
    list_display = ('name', 'id')
