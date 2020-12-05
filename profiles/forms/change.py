
from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model
from profiles import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _
from profiles import widgets


User = get_user_model()


class ChangeRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.wrapper_class = 'row'
        # self.helper.label_class = 'col-md-6'
        # self.helper.field_class = 'col-md-6'
        self.fields['new'].label = False
        self.helper.layout = Layout(
                            Field('new'),

        )  # layout

    class Meta:
        model = models.RoleChangeRequest
        fields = ["new", "user"]


class DeclareRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                None,
                Field("new")),
                Submit("Wybierz role", "Wybierz role"),
        )

    class Meta:
        model = models.RoleChangeRequest
        fields = ["new"]
