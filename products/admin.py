from django.contrib import admin
from . import models 
from utils import linkify
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from django.contrib import admin
from django.utils.safestring import mark_safe


@admin.register(models.Product)
class ProductModel(admin.ModelAdmin):
    list_display = ('title', 'active', 'subtitle', 'place', 'person', 'teaser')
    search_fields = ('tags__name',)


@admin.register(models.UserRequest)
class UserRequestModel(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_display = ('user', linkify('product'), 'date')
    autocomplete_fields = ('user',)
    readonly_fields = ('data_prettified',)

    def data_prettified(self, instance):
        """Function to display pretty version of our data"""

        # Convert the data to sorted, indented JSON
        response = json.dumps(instance.raw_body, sort_keys=True, indent=2)

        # Truncate the data. Alter as needed
        response = response[:5000]

        # Get the Pygments formatter
        formatter = HtmlFormatter(style='colorful')

        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)

        # Get the stylesheet
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        # Safe the output
        return mark_safe(style + response)


@admin.register(models.Tag)
class TagModel(admin.ModelAdmin):
    list_display = ('name',)
