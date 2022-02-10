from __future__ import unicode_literals
from email.policy import default
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model
from profiles import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _
from profiles import widgets
from crispy_forms.bootstrap import InlineRadios
from clubs.models import Team
User = get_user_model()
from dataclasses import dataclass
import collections.abc
from django.core.exceptions import ValidationError


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

CSS_MANDATORY_FIELD_CLASS = 'mandatory'


@dataclass
class FieldConfig:
    required = True
    label = False
    help_text = ''
    placeholder = ''


class VerificationForm(forms.ModelForm):
    settings = {
        'team_club_league_voivodeship_ver': {
            'placeholder': 'np. WKS Wrocław, IV Liga, donlośląskie',
            'required': False
        },
        'team': {
            'required': False
        },
        'has_team': {
            'initial': 'tak mam klub',
            'required': False},
        'team_not_found': {
            'label': 'zaznacz jeśli nie znalazłeś swojego klubu na liście',
            'required': False}
    }

    custom_settings = None

    building_fields = []

    CHOICES = (('tak mam klub', 'tak mam klub'), ('Nie mam klubu', 'Nie mam klubu'))
    team = forms.ModelChoiceField(queryset=Team.objects.all())
    has_team = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    team_not_found = forms.BooleanField()
    # DEFAULT_FIELDS = ['team_not_found', 'team', 'has_team']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_field_settings = FieldConfig()
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = 'col-md-2 p-1'
        self.helper.field_class = 'col-12 p-1'
        self.set_fields_rules()

        self.helper.layout = self.build_layout()

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get("team")
        text_club = cleaned_data.get("team_club_league_voivodeship_ver")

        if not team and not text_club:
            msg = "Wybierz klub z listy bądź wprowadź klub ręcznie"
            self.add_error('team', msg)
            self.add_error("team_club_league_voivodeship_ver", msg)

    def set_fields_rules(self):
        """ Configure fields"""
        settings = self.settings.copy()
        if self.custom_settings:
            update(settings, self.custom_settings)

        print(settings)
        for field_name, options in settings.items():
            self.fields[field_name].required = options.get("required", self.default_field_settings.required)
            self.fields[field_name].label = options.get("label", self.default_field_settings.label)
            self.fields[field_name].help_text = options.get("help_text", self.default_field_settings.help_text)
            self.fields[field_name].widget.attrs['placeholder'] = options.get("placeholder", self.default_field_settings.placeholder)
            if initial := options.get('initial'):
                self.fields[field_name].initial = initial
                
    def build_layout(self):
        common_fields = [''] + [cfg.get('field_class', Field)(fn, warpper_class='row', css_class=cfg.get('css_class')) for fn, cfg in self.building_fields]
        return Layout(
            Fieldset(*common_fields),
            
            InlineRadios("has_team", id="team_choice"),
            Div(
                Field("team"),
                Field("team_not_found"),
                css_id='select_team_div'
            ),
            Div(
                Field("team_club_league_voivodeship_ver"),
                css_id='text_team_div'
            )     
        )


class ClubVerificationForm(VerificationForm):
    custom_settings = {
        'team_club_league_voivodeship_ver': {'help_text': 'Który klub reprezentujesz'}, 
        'club_role': {'help_text': 'Jaka rolę pełnisz w klubie'},
        'team': {'help_text': "Team którym zarządzasz"},
    }

    building_fields = [
        ('club_role', {}),
    ]

    class Meta:
        model = models.ClubProfile
        fields = models.ClubProfile.VERIFICATION_FIELDS


class CoachVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    custom_settings = [
        ('team_club_league_voivodeship_ver', {'help_text': 'Który klub reprezentujesz'}),
        ('birth_date', {'placeholder': '1998-09-24', 'help_text': _('Data urodzenia')}),
        ('country', {'help_text': _('Kraj pochodzenia')}),
    ]

    class Meta:
        model = models.CoachProfile
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        fields = models.CoachProfile.VERIFICATION_FIELDS


class PlayerVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    custom_settings = [
            ('birth_date', {'placeholder': '1998-09-24', 'help_text': _('Kraj pochodzenia')}),
            ('position_raw', {}),
            ('team', {'help_text': 'Wybierz z listy rozwijanej'}),
            ('country', {'help_text': _('Data urodzenia')}),
            ('has_team', {})
        ]
    building_fields = (
        ('position_raw', {}), 
        ('birth_date', {}), 
        ('country', {})
    )

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        fields = models.PlayerProfile.VERIFICATION_FIELDS + ['position_raw']
