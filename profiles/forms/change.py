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
from django_countries.widgets import CountrySelectWidget

from profiles import models, widgets

User = get_user_model()


class ChangeRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.wrapper_class = 'row'
        # self.helper.label_class = 'col-md-6'
        # self.helper.field_class = 'col-md-6'
        self.fields["new"].label = False

        self.helper.layout = Layout(
            Field("new"),
        )  # layout

    class Meta:
        model = models.RoleChangeRequest
        fields = ["new", "user"]


class DeclareRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["new"].label = False
        self.helper.layout = Layout(
            Fieldset(None, Field("new")),
        )

    class Meta:
        model = models.RoleChangeRequest
        fields = ["new"]
