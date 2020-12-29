

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
from django.utils import timezone


User = get_user_model()


def year_choices():
    now = timezone.now().year - 10
    start = now - 40
    return [(i, i) for i in list(range(start, now + 1))]


class AnnouncementForm(forms.ModelForm):

    building_fields = [
        ('country', 'Kraj', None, {}),
        ('club', 'Klub', None, {}),
        ('league', 'Poziom rozgrywkowy', None, {}),
        ('positions', 'Pozycje(3)', 'multiple', {'data-actions-box': "true", 'data-max-options': "2"}),
        ('voivodeship', 'Województwo',  None, {}),
        ('year_from', 'Rocznik od',  None, {}),
        ('year_to', 'Rocznik do',  None, {}),
        ('address', 'np. Wroclaw, Polska', None, {}),
        ('seniority', 'Rozgrywki młodzieżowe / Rozgrywki seniorskie', None,  {}),
        ('gender', 'Mężczyźni / Kobiety', None, {}),
        ('body', 'Wprowadź najważniejsze informacje na temat Twojego klubu oraz testów', None, {}),
        ('www', 'Możesz dodać link do ogłoszenia naboru na stronie lub facebooku, lub dodaj adres www klubu', None, {}),
    ]

    def __init__(self, *args, **kwargs):
        print(year_choices())
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-12 col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-12 col-md-8'
        self.helper.wrapper_class = 'row'

        self.fields['year_from'] = forms.ChoiceField(choices=year_choices())
        self.fields['year_to'] = forms.ChoiceField(choices=year_choices())
        self.set_fields_rules()
        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):

        self.fields['year_from'].required = True
        self.fields['year_from'].label = 'Rocznik od'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['year_from'].help_text = False

        self.fields['year_to'].required = True
        self.fields['year_to'].label = 'Rocznik do'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['year_to'].help_text = False

        self.fields['league'].required = True
        self.fields['league'].label = 'Poziom rozgrywkowy'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = False

        self.fields['club'].required = True
        self.fields['club'].label = 'Klub'
        self.fields['club'].help_text = False

        self.fields['country'].required = True
        self.fields['country'].label = 'Kraj'
        self.fields['country'].help_text = False

        self.fields['voivodeship'].required = True
        self.fields['voivodeship'].label = 'Województwo'
        self.fields['voivodeship'].help_text = False

        self.fields['seniority'].required = True
        self.fields['seniority'].label = 'Rozgrywki młodzieżowe / Rozgrywki seniorskie'
        self.fields['seniority'].help_text = False

        self.fields['gender'].required = True
        self.fields['gender'].label = 'Mężczyźni / Kobiety'
        self.fields['gender'].help_text = False

        self.fields['address'].required = True
        self.fields['address'].label = 'Adres testów'
        self.fields['address'].help_text = False

        self.fields['www'].required = False
        self.fields['www'].label = 'Link www ogłoszenia / strony internetowej klubu (opcjonalnie)'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['www'].help_text = False

        self.fields['body'].required = True
        self.fields['body'].label = 'Informacje o klubie / testach'
        self.fields['body'].help_text = False

        self.fields['positions'].required = True
        self.fields['positions'].label = 'Pozycje'
        self.fields['positions'].help_text = False

    def build_verification_form(self):
                               
        fds = [''] + [Field(fn, wrapper_class='row', placeholder=fp, title=fp, css_class=fc, **kwargs) for fn, fp, fc, kwargs in self.building_fields]
        return Fieldset(*fds)

    class Meta:
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        model = models.Announcement
        fields = ['country', 'club', 'league', 'voivodeship', 'seniority', 'gender', 'www', 'body', 'address', 'positions', 'year_from', 'year_to']
        exclude = ['creator']
