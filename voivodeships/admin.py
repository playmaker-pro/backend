from django.contrib import admin

from .models import Voivodeships


@admin.register(Voivodeships)
class VoivodeshipsAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
