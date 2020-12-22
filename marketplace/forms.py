

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


class AnnouncementForm(forms.ModelForm):

    building_fields = [

        ('team_club_league_voivodeship_ver', 'np. MKS Zbyszkowo, we Wrocławiu', None),
        ('club_role', None, None),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-md-2 p-1'
        self.helper.field_class = 'col-12 p-1'
        self.set_fields_rules()

        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['team_club_league_voivodeship_ver'].help_text = None

    def build_verification_form(self):

        fds = [''] + [Field(fn, warpper_class='row', placeholder=fp, css_class=fc) for fn, fp, fc in self.building_fields]
        return Fieldset(*fds)
    class Meta:
        model = models.ClubProfile
        fields = models.ClubProfile.VERIFICATION_FIELDS
