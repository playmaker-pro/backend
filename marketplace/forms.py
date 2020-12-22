

from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model
from . import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _
from profiles import widgets
from django_countries.widgets import CountrySelectWidget


User = get_user_model()


class AnnouncementForm(forms.ModelForm):

    building_fields = [
        ('country', 'Kraj', None, {}),
        ('club', 'Klub', None, {}),
        ('league', 'Poziom rozgrywkowy', None, {}),
        ('positions', 'Pozycje(3)', 'multiple', {'data-actions-box': "true", 'data-max-options': "2"}),
        ('voivodeship', 'Województwo',  None, {}),
        ('address', 'np. Wroclaw, Polska', None, {}),
        ('seniority', 'Rozgrywki młodzieżowe / Rozgrywki seniorskie', None,  {}),
        ('gender', 'Mężczyźni / Kobiety', None, {}),
        ('body', 'Wprowadź najważniejsze informacje na temat Twojego klubu oraz testów', None, {}),
        ('www', 'Możesz dodać link do ogłoszenia naboru na stronie lub facebooku, lub dodaj adres www klubu', None, {}),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-md-2 p-1'
        self.helper.field_class = 'col-12'
        self.set_fields_rules()

        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):
        self.fields['league'].required = True
        self.fields['league'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = 'Poziom rozgrywkowy'

        self.fields['club'].required = True
        self.fields['club'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['club'].help_text = 'Klub'

        self.fields['country'].required = True
        self.fields['country'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['country'].help_text = 'Kraj'

        self.fields['voivodeship'].required = True
        self.fields['voivodeship'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['voivodeship'].help_text = 'Województwo'

        self.fields['seniority'].required = True
        self.fields['seniority'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['seniority'].help_text = 'Rozgrywki młodzieżowe / Rozgrywki seniorskie'

        self.fields['gender'].required = True
        self.fields['gender'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['gender'].help_text = 'Mężczyźni / Kobiety'

        self.fields['address'].required = True
        self.fields['address'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['address'].help_text = 'np. Wroclaw, Polska'

        self.fields['www'].required = False
        self.fields['www'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['www'].help_text = 'Link www ogłoszenia / strony internetowej klubu (opcjonalnie)'

        self.fields['body'].required = True
        self.fields['body'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['body'].help_text = 'Informacje o klubie / testach'

        self.fields['positions'].required = True
        self.fields['positions'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['positions'].help_text = 'Pozycje'

    def build_verification_form(self):

        fds = [''] + [Field(fn, warpper_class='row', placeholder=fp, title=fp, css_class=fc, **kwargs) for fn, fp, fc, kwargs in self.building_fields]
        return Fieldset(*fds)

    class Meta:
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        model = models.Announcement
        fields = ['country', 'club', 'league', 'voivodeship', 'seniority', 'gender', 'www', 'body', 'address', 'positions']
        exclude = ['creator']