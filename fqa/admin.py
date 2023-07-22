import json

# Register your models here.
from django.contrib import admin
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

from utils import linkify

from . import models


@admin.register(models.QuestionAnswer)
class QuestionAnswerModel(admin.ModelAdmin):
    list_display = ("id", "visible", "question_html", "answer_html")
