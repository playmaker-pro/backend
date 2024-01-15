from django.contrib import admin

from app.utils.admin import json_filed_data_prettified
from utils import linkify

from . import models


@admin.register(models.PlaysConfig)
class PlaysConfigAdmin(admin.ModelAdmin):
    list_display = ("main_league",)
