from __future__ import unicode_literals

import collections.abc
from dataclasses import dataclass

from clubs.models import Club, Season, TeamHistory
from clubs.models import TeamHistory as Team
from crispy_forms.bootstrap import (
    Alert,
    AppendedText,
    FormActions,
    InlineRadios,
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
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django_countries.widgets import CountrySelectWidget
from profiles import models, widgets
from profiles.forms.fields.custom import (
    ClubModelChoiceFieldNoValidation,
    ModelChoiceFieldNoValidation,
)
from profiles.services import ProfileVerificationService
from utils import update_dict_depth


User = get_user_model()


CSS_MANDATORY_FIELD_CLASS = "mandatory"


# A short cut to hide query logic behind function
def get_all_teams():
    return Team.objects.all()


def get_all_clubs():
    teams = cache.get("all_clubs")
    if not teams:
        teams = Club.objects.all()
        cache.set("all_clubs", teams)
    return teams


def get_season_with_team_history():
    # ths = [th.season.name for th in TeamHistory.objects.all().distinct("season")]
    return Season.objects.filter(name__in="ths").order_by("name")


@dataclass
class FieldConfig:
    required = True
    label = False
    help_text = ""
    placeholder = ""


class VerificationForm(forms.ModelForm):
    """
    settings describes how filed will be build.
    """

    CHOICES_HAS_TEAM = (
        ("tak mam klub", "tak mam klub"),
        ("Nie mam klubu", "Nie mam klubu"),
    )

    settings = {
        "team_club_league_voivodeship_ver": {
            "placeholder": "np. WKS Wrocław, IV Liga, donlośląskie",
            "required": False,
        },
        "team": {"required": False},
        "season": {"required": False},
        "has_team": {"initial": "tak mam klub", "required": False},
        "team_not_found": {
            "label": "zaznacz jeśli nie znalazłeś swojego klubu na liście",
            "required": False,
        },
    }
    custom_settings = None

    building_fields = []

    team = ModelChoiceFieldNoValidation()
    has_team = forms.ChoiceField(choices=CHOICES_HAS_TEAM, widget=forms.RadioSelect)
    team_not_found = forms.BooleanField()
    season = forms.ModelChoiceField(
        queryset=get_season_with_team_history(),
        widget=forms.Select(attrs={"data-live-search": "true"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_field_settings = FieldConfig()
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.label_class = "col-md-2 p-1"
        self.helper.field_class = "col-12 p-1"
        self.set_fields_rules()
        self.helper.layout = self.build_layout()

    def save(self, commit=True):
        """saves verification using verification service."""
        instance = super().save(commit=False)
        service = ProfileVerificationService(instance)
        data = self.cleaned_data

        service.update_verification_data(data, requestor=self.instance.user)
        service.verify()
        service.update_verification_status(status=service.user.state)

        if commit:
            instance.save()
        return instance

    def clean(self):
        """Clean some of the fields"""
        cleaned_data = super().clean()
        team = cleaned_data.get("team")
        text_club = cleaned_data.get("team_club_league_voivodeship_ver")

        if not team and not text_club:
            msg = "Wybierz klub z listy bądź wprowadź klub ręcznie"
            self.add_error("team", msg)
            self.add_error("team_club_league_voivodeship_ver", msg)

    def set_fields_rules(self):
        """Configure fields"""
        settings = self.settings.copy()
        if self.custom_settings:
            update_dict_depth(settings, self.custom_settings)
        for field_name, options in settings.items():
            self.fields[field_name].required = options.get(
                "required", self.default_field_settings.required
            )
            self.fields[field_name].label = options.get(
                "label", self.default_field_settings.label
            )
            self.fields[field_name].help_text = options.get(
                "help_text", self.default_field_settings.help_text
            )
            self.fields[field_name].widget.attrs["placeholder"] = options.get(
                "placeholder", self.default_field_settings.placeholder
            )

            if initial := options.get("initial"):
                self.fields[field_name].initial = initial

    def build_layout(self):
        common_fields = [""] + [
            cfg.get("field_class", Field)(
                fn, warpper_class="row", css_class=cfg.get("css_class")
            )
            for fn, cfg in self.building_fields
        ]
        return Layout(
            Fieldset(*common_fields),
            InlineRadios("has_team", id="team_choice"),
            Div(
                Field("season"),
                Field("team"),
                Field("team_not_found"),
                css_id="select_team_div",
            ),
            Div(Field("team_club_league_voivodeship_ver"), css_id="text_team_div"),
        )


class ClubVerificationForm(VerificationForm):
    custom_settings = {
        "team_club_league_voivodeship_ver": {"help_text": "Który klub reprezentujesz"},
        "club_role": {"help_text": "Jaka rolę pełnisz w klubie"},
        "team": {"help_text": "Klub którym zarządzasz"},
    }

    team = ClubModelChoiceFieldNoValidation()
    # rkesik: I've left that just as a reference
    # team = forms.ModelChoiceField(
    #     queryset=Club.objects.all(),
    #     widget=forms.Select(attrs={"data-live-search": "true"}),
    # )

    building_fields = [
        ("club_role", {}),
    ]

    class Meta:
        model = models.ClubProfile
        fields = models.ClubProfile.VERIFICATION_FIELDS + [
            "team_club_league_voivodeship_ver"
        ]


class CoachVerificationForm(VerificationForm):
    birth_date = forms.DateField(
        input_formats=["%Y-%m-%d"], widget=widgets.BootstrapDateTimePickerInput()
    )

    building_fields = (("birth_date", {}), ("country", {}), ("licence", {}))

    custom_settings = {
        "team_club_league_voivodeship_ver": {"help_text": "Który klub reprezentujesz"},
        "birth_date": {"placeholder": "1998-09-24", "help_text": _("Data urodzenia")},
        "country": {"help_text": _("Kraj pochodzenia")},
        "licence": {"placeholder": "np. UEFA B", "help_text": _("Licencjaa")},
    }

    class Meta:
        model = models.CoachProfile
        widgets = {
            "country": CountrySelectWidget(layout="{widget}"),
        }
        fields = models.CoachProfile.VERIFICATION_FIELDS + [
            "team_club_league_voivodeship_ver"
        ]


class PlayerVerificationForm(VerificationForm):
    custom_settings = {
        "birth_date": {"placeholder": "1998-09-24", "help_text": _("Data urodzenia")},
        "position_raw": {"help_text": _("Pozycja")},
        "team": {"help_text": _("Wybierz z listy rozwijanej")},
        "country": {"help_text": _("Kraj pochodzenia")},
        "has_team": {},
    }

    building_fields = (("position_raw", {}), ("birth_date", {}), ("country", {}))

    birth_date = forms.DateField(widget=widgets.BootstrapDateTimePickerInput())

    class Meta:
        model = models.PlayerProfile
        widgets = {
            "country": CountrySelectWidget(layout="{widget}"),
        }
        fields = models.PlayerProfile.VERIFICATION_FIELDS + [
            "position_raw",
            "team_club_league_voivodeship_ver",
        ]
