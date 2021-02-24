from django.contrib import admin

# Register your models here.
from django.contrib import admin
from . import models 
from utils import linkify
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from django.contrib import admin
from django.utils.safestring import mark_safe


@admin.register(models.QuestionAnswer)
class QuestionAnswerModel(admin.ModelAdmin):
    list_display = ('id', 'visible', 'question_html', 'answer_html')
