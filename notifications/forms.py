from __future__ import unicode_literals

from crispy_forms.bootstrap import (
    Alert,
    AppendedText,
    FormActions,
    PrependedText,
    Tab,
    TabHolder,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    HTML,
    Button,
    Div,
    Field,
    Fieldset,
    Layout,
    MultiField,
    Row,
    Submit,
)
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from profiles import widgets

from . import models

User = get_user_model()


class NotificationSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "",
                Div(
                    Div(
                        Field("weekly_report", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    # css_class='card',
                ),
            )
        )

    class Meta:
        model = models.NotificationSetting
        fields = ["weekly_report"]
