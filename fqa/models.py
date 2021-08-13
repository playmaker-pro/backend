from django.db import models


class QuestionAnswer(models.Model):
    visible = models.BooleanField(default=True)
    question_html = models.TextField(null=True, blank=True)
    answer_html = models.TextField(null=True, blank=True)
