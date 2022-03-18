

from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model

from clubs.models import Voivodeship
from profiles.models import CoachProfile
from . import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _
from profiles import widgets
from django_countries.widgets import CountrySelectWidget
from django.utils import timezone

User = get_user_model()

VOIVODESHIPS = [
    "dolnośląskie",
    "kujawskopomorskie",
    "lubelskie",
    "lubuskie",
    "łódzkie ",
    "małopolskie ",
    "mazowieckie",
    "opolskie",
    "podkarpackie",
    "podlaskie",
    "pomorskie",
    "śląskie",
    "świętokrzyskie",
    "warmińskomazurskie",
    "wielkopolskie",
    "zachodniopomorskie",
]


def year_choices():
    now = timezone.now().year - 10
    start = now - 40
    return [(i, i) for i in list(range(start, now + 1))]


class ClubForPlayerAnnouncementForm(forms.ModelForm):
    building_fields = [

        ('Teams', "Dużyna", None, {}),
        ('country', 'Kraj', None, {}),
        ('club', 'Klub', None, {}),
        ('league', 'Poziom rozgrywkowy', None, {}),
        ('positions', 'Pozycje', 'multiple', {'data-actions-box': "true"}),
        ('voivodeship', 'Województwo',  None, {}),
        ('year_from', 'Rocznik od',  None, {}),
        ('year_to', 'Rocznik do',  None, {}),
        ('address', 'np. Wroclaw, Polska', None, {}),
        ('seniority', 'Rozgrywki młodzieżowe / Rozgrywki seniorskie', None,  {}),
        ('gender', 'Mężczyźni / Kobiety', None, {}),
        ('body', 'Wprowadź najważniejsze informacje na temat Twojego klubu oraz testów', None, {}),
        ('www', "http://stronaklubu.pl", None, {}),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-12 col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-12 col-md-8'
        self.helper.wrapper_class = 'row'

        self.fields['year_from'] = forms.ChoiceField(choices=year_choices())
        self.fields['Teams'] = forms.ChoiceField(choices=[])
        self.fields['year_to'] = forms.ChoiceField(choices=year_choices())
        self.set_fields_rules()
        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):

        self.fields['Teams'].required = True
        self.fields['Teams'].label = "Drużyna"

        self.fields['year_from'].required = True
        self.fields['year_from'].label = 'Rocznik od'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['year_from'].help_text = False

        self.fields['year_to'].required = True
        self.fields['year_to'].label = 'Rocznik do'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['year_to'].help_text = False

        self.fields['league'].widget = forms.HiddenInput()
        self.fields['league'].label = 'Poziom rozgrywkowy'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = False

        self.fields['club'].widget = forms.HiddenInput()
        self.fields['club'].label = 'Klub'
        self.fields['club'].help_text = False

        self.fields['country'].widget = forms.HiddenInput()
        self.fields['country'].label = 'Kraj'
        self.fields['country'].help_text = False

        self.fields['voivodeship'].widget = forms.HiddenInput()
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
        widgets = {'country': CountrySelectWidget(layout='{widget}'),
                   'body': forms.Textarea(attrs={'rows': 5})
                   }
        model = models.ClubForPlayerAnnouncement
        fields = ['country', 'club', 'league', 'voivodeship', 'seniority', 'gender', 'www', 'body', 'address', 'positions', 'year_from', 'year_to']
        exclude = ['creator']


class PlayerForClubAnnouncementForm(forms.ModelForm):
    building_fields = [

        ('position', 'Pozycja', None, {}),
        ('voivodeship', 'Województwo', None, {}),
        ('league', 'Poziom rozgrywkowy', None, {}),
        ('target_league', 'Cel poszukiwań', None, {}),
        ('address', 'np. Wrocław', None, {}),
        ('practice_distance', 'Maksymalna odległość dojazdu', None, {}),
        ('body', 'Opisz krótko swoje oczekiwania', None, {}),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-12 col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-12 col-md-8'
        self.helper.wrapper_class = 'row'

        self.set_fields_rules()
        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):
        self.fields['position'].required = True
        self.fields['position'].label = 'Pozycja'
        self.fields['position'].help_text = False

        self.fields['voivodeship'].required = True
        self.fields['voivodeship'].label = 'Województwo'
        self.fields['voivodeship'].help_text = False

        self.fields['address'].required = True
        self.fields['address'].label = 'Miejscowość z której dojeżdżasz na trening'
        self.fields['address'].help_text = False

        self.fields['practice_distance'].required = True
        self.fields['practice_distance'].label = 'Maksymalna odległość dojazdu w km'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['practice_distance'].help_text = False

        self.fields['target_league'].required = True
        self.fields['target_league'].label = 'Cel poszukiwań'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['target_league'].help_text = False

        self.fields['league'].required = False
        self.fields['league'].label = 'Poziom rozgrywkowy'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = False
        self.fields['league'].widget = forms.HiddenInput()

        self.fields['body'].required = True
        self.fields['body'].label = 'Oczekiwania'
        self.fields['body'].help_text = False

    def build_verification_form(self):
        fds = [''] + [Field(fn, wrapper_class='row', placeholder=fp, title=fp, css_class=fc, **kwargs) for fn, fp, fc, kwargs in self.building_fields]
        return Fieldset(*fds)

    class Meta:
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }
        model = models.PlayerForClubAnnouncement
        fields = ['position', 'voivodeship', 'address', 'practice_distance', 'target_league', 'league', 'body']
        exclude = ['creator']


class CoachForClubAnnouncementForm(forms.ModelForm):

    building_fields = [
        ('lic_type', 'Typ licencji', None, {}),
        ('voivodeship', 'Województwo', None, {}),
        ('address', 'np. Wrocław', None, {}),
        ('practice_distance', 'Maksymalna odległość dojazdu', None, {}),
        ('league', 'Obecna liga', None, {}),
        ('target_league', 'Cel poszukiwań', None, {}),
        ('body', 'Opisz krótko swoje dotychczasowe osiągniecia oraz oczekiwania', None, {}),

    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-12 col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-12 col-md-8'
        self.helper.wrapper_class = 'row'

        self.set_fields_rules()
        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):
        self.fields['lic_type'].required = True
        self.fields['lic_type'].label = 'Typ licencji'
        self.fields['lic_type'].help_text = False

        self.fields['voivodeship'].required = True
        self.fields['voivodeship'].label = 'Województwo'
        self.fields['voivodeship'].help_text = False

        self.fields['address'].required = True
        self.fields['address'].label = 'Miejscowość z której dojeżdżasz na trening'
        self.fields['address'].help_text = False

        self.fields['practice_distance'].required = True
        self.fields['practice_distance'].label = 'Maksymalna odległość dojazdu w km'
        self.fields['practice_distance'].help_text = False

        self.fields['league'].required = False
        self.fields['league'].label = 'Obecna liga'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = False
        self.fields['league'].widget = forms.HiddenInput()

        self.fields['target_league'].required = True
        self.fields['target_league'].label = 'Cel poszukiwań'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['target_league'].help_text = False

        self.fields['body'].required = True
        self.fields['body'].label = 'Opis ogłoszenia'
        self.fields['body'].help_text = False

    def build_verification_form(self):
        fds = [''] + [Field(fn, wrapper_class='row', placeholder=fp, title=fp, css_class=fc, **kwargs) for fn, fp, fc, kwargs in self.building_fields]
        return Fieldset(*fds)

    class Meta:
        # widgets = {'country': CountrySelectWidget(layout='{widget}')}
        widgets = {'body': forms.Textarea(attrs={'rows': 5})}
        model = models.CoachForClubAnnouncement
        fields = ['lic_type', 'voivodeship', 'address', 'practice_distance', 'target_league', 'league', 'body']
        exclude = ['creator']


class ClubForCoachAnnouncementForm(forms.ModelForm):
    building_fields = [
        ('club', 'Klub', None, {}),
        ('league', 'Poziom rozgrywkowy', None, {}),
        ('voivodeship', 'Województwo', None, {}),
        ('lic_type', 'Typ licencji', None, {}),
        ('seniority', 'Rozgrywki młodzieżowe / Rozgrywki seniorskie', None, {}),
        ('gender', 'Mężczyźni / Kobiety', None, {}),
        ('body', 'Opisz krótko oczekiwania wobec trenerów', None, {}),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-12 col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-12 col-md-8'
        self.helper.wrapper_class = 'row'

        self.set_fields_rules()
        self.helper.layout = self.build_verification_form()

    def set_fields_rules(self):
        self.fields['club'].required = True
        self.fields['club'].label = 'Klub'
        self.fields['club'].help_text = False

        self.fields['league'].required = True
        self.fields['league'].label = 'Poziom rozgrywkowy'  # '<i class="icofont-ui-user-group"></i>'
        self.fields['league'].help_text = False

        self.fields['voivodeship'].required = True
        self.fields['voivodeship'].label = 'Województwo'
        self.fields['voivodeship'].help_text = False

        # self.fields['lic_type'] = forms.ChoiceField(widget=forms.Select(), choices=CoachProfile.LICENCE_CHOICES)
        self.fields['lic_type'].required = True
        self.fields['lic_type'].label = 'Typ licencji'
        self.fields['lic_type'].help_text = False

        self.fields['seniority'].required = True
        self.fields['seniority'].label = 'Rozgrywki młodzieżowe / Rozgrywki seniorskie'
        self.fields['seniority'].help_text = False

        self.fields['gender'].required = True
        self.fields['gender'].label = 'Mężczyźni / Kobiety'
        self.fields['gender'].help_text = False

        self.fields['body'].required = True
        self.fields['body'].label = 'Oczekiwania'
        self.fields['body'].help_text = False

    def build_verification_form(self):
        fds = [''] + [Field(fn, wrapper_class='row', placeholder=fp, title=fp, css_class=fc, **kwargs) for fn, fp, fc, kwargs in self.building_fields]
        return Fieldset(*fds)

    class Meta:
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }
        model = models.ClubForCoachAnnouncement
        fields = ['club', 'league', 'lic_type', 'voivodeship', 'seniority', 'gender', 'body']
        exclude = ['creator']
