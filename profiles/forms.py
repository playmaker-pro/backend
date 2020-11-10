from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions
from django.contrib.auth import get_user_model
from . import models
from django_countries.widgets import CountrySelectWidget


User = get_user_model()


class ChangeRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Zmien role w serwisie',
                # Field("current"),
                Field("new")),
                Submit("Zgloś zmiane", "Zgloś zmiane profilu", css_class="btn-success"),
        )

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
                Submit("Wybierz role", "Wybierz role", css_class="btn-success"),
        )

    class Meta:
        model = models.RoleChangeRequest
        fields = ["new"]


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Dane konta',
                Field("email"),
                Field("picture"))
        )

    class Meta:
        model = User
        fields = ["email", "picture"]


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("bio"),
            Submit("update", "Update", css_class="btn-success"),
        )

    class Meta:
        model = models.StandardProfile
        fields = ["bio"]


class GuestProfileForm(ProfileForm):
    pass

phone_number_format = "+[0-9] [0-9]{3}-[0-9]{3}-[0-9]{3}"


class CoachProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Podstawowe informacje',
                Field("bio"),
                Field("birth_date")
            ),
            Fieldset(
                'Informacje dodatkowe',
                Field("facebook_url"),
                Field("soccer_goal"),
                Field("phone")
            ),
            Submit("update", "Update", css_class="btn-success"),
        )

    class Meta:
        model = models.CoachProfile
        fields = ["bio", "birth_date", "facebook_url", "soccer_goal", "phone"]

class ClubProfileForm(ProfileForm): 
    pass


class PlayerProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.layout = Layout(
            Fieldset(
                'Podstawowe info',
                Field("birth_date"),
                Field("country"),
                Field("club_raw"),
            ),

            Fieldset(
                'Dane biometryczne',
                Field('bio'),
                Field("height"),
                Field("weight"),
            ),
            Field("league_raw"),
            Field("voivodeship_raw"),
            Field("formation"),
            Field("prefered_leg"),
            Field("position_raw"),
            Field("card"),
            Field("phone"),
            Field("transfer_status"),
            Submit("update", "Update", css_class="btn-success"),
        )

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget()}
        fields = [
            "bio",
            'country',
            "birth_date",
            "height",
            "weight",
            "formation",
            "prefered_leg",
            "card",
            "phone",
            "transfer_status",
            "club_raw",
            "league_raw",
            "voivodeship_raw",
            "position_raw",
        ]
