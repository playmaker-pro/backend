

from django.contrib import admin
from utils import linkify
from app.admin_utils import json_filed_data_prettified
from . import models


@admin.register(models.PlaysConfig)
class PlaysConfigAdmin(admin.ModelAdmin):
    list_display = (
        "main_league",

    )
