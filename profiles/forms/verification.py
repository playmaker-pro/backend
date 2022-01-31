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

User = get_user_model()


CSS_MANDATORY_FIELD_CLASS = 'mandatory'


class VerificationForm(forms.ModelForm):

    building_fields = None

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
        fds = [''] + [cfg.get('field_class', Field)(fn, warpper_class='row', placeholder=cfg.get('placeholder'), css_class=cfg.get('css_class')) for fn, cfg in self.building_fields]
        return Fieldset(*fds)


class ClubVerificationForm(VerificationForm):
    building_fields = [
        ('team_club_league_voivodeship_ver', {'placeholder': 'np. MKS Zbyszkowo, we Wrocławiu'}),
        ('club_role', {}),
    ]

    def set_fields_rules(self):
        self.fields['club_role'].required = True
        self.fields['club_role'].label = False
        self.fields['club_role'].help_text = 'Jaka rolę pełnisz w klubie'

        self.fields['team_club_league_voivodeship_ver'].help_text = 'Który klub reprezentujesz'
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = False

    class Meta:
        model = models.ClubProfile
        fields = models.ClubProfile.VERIFICATION_FIELDS


class CoachVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    building_fields = [
        ('birth_date', {'placeholder': '1998-09-24'}),
        ('team_club_league_voivodeship_ver', {'placeholder': 'np. MKS Zbyszkowo, we Wrocławiu'}),
        ('country', {}),
    ]

    def set_fields_rules(self):
        self.fields['birth_date'].help_text = _('Data urodzenia')
        self.fields['birth_date'].required = True
        self.fields['birth_date'].label = False  # '<i class="icofont-birthday-cake"></i>'

        self.fields['country'].required = True
        self.fields['country'].label = False  # '<i class="icofont-map"></i>'
        self.fields['country'].help_text = _('Kraj pochodzenia')

        self.fields['team_club_league_voivodeship_ver'].help_text = 'Który klub reprezentujesz'
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = False  # '<i class="icofont-team-alt"></i>'

    class Meta:
        model = models.CoachProfile
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        fields = models.CoachProfile.VERIFICATION_FIELDS
from clubs.models import Team

class PlayerVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    building_fields = [
            ('birth_date', {'placeholder': '1998-09-24'}),
            ('position_raw', {}),
            ('team_club_league_voivodeship_ver', {'placeholder': 'np. MKS Zbyszkowo, we Wrocławiu'}),
            ('country', {}),
            ('team', {}),
            ('has_team', {'field_class': InlineRadios})
        ]
    CHOICES = (('tak mam klub', 'tak mam klub'), ('Nie mam klubu','Nie mam klubu'))
    team = forms.ModelChoiceField(queryset=Team.objects.all())
    has_team = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    def set_fields_rules(self):
        self.fields['team'].help_text = 'team w koryt'
        self.fields['team'].required = True
        self.fields['team'].label = False  # '<i class="icofont-field"></i>'

        self.fields['position_raw'].help_text = 'Pozycja na której obecnie grasz'
        self.fields['position_raw'].required = True
        self.fields['position_raw'].label = False  # '<i class="icofont-field"></i>'

        self.fields['birth_date'].help_text = _('Data urodzenia')
        self.fields['birth_date'].required = True
        self.fields['birth_date'].label = False  # '<i class="icofont-birthday-cake"></i>'

        self.fields['country'].required = True
        self.fields['country'].label = False  # '<i class="icofont-map"></i>'
        self.fields['country'].help_text = _('Kraj pochodzenia')

        self.fields['team_club_league_voivodeship_ver'].help_text = _('Klub w którym grasz / nie mam jeszcze klubu')
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = False  # '<i class="icofont-team-alt"></i>'

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget(layout='{widget}')}
        fields = models.PlayerProfile.VERIFICATION_FIELDS + ['position_raw', 'team']
