from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model
from . import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class ChangeRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.wrapper_class = 'row'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-6'

        self.helper.layout = Layout(
            Div(
                Div(
                    Fieldset(
                        _('<h2 class="form-section-title">Zmien role w serwisie</h2>'),
                        Div(
                            Field('new', wrapper_class='row', selected='T'),
                        ),
                        css_class='col-md-6',
                    ),  # fieldset
                    css_class='row'
                ),  # div
                #css_class='card',
            )  # div master div
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


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Div(             
                    Div(
                        Div('first_name', css_class="col-sm-6"),
                        Div('last_name', css_class="col-sm-6"),
                        Div('email', css_class="col-sm-6"),
                        Div('picture', css_class="col-sm-6", ),
                        css_class='row',
                    ),
                    #css_class='card',
                ),
            )
        )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', "email", "picture"]


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
            Submit("update", "Update"),
        )

    class Meta:
        model = models.CoachProfile
        fields = ["bio", "birth_date", "facebook_url", "soccer_goal", "phone"]


class ClubProfileForm(ProfileForm):
    pass


class VerificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-6'

        self.fields['birth_date'].required = True
        self.fields['country'].required = True
        self.fields['country'].initial = 'PL'
        self.fields['position_raw'].required = True
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = 'Gdzie grasz'

        self.helper.layout = Fieldset(
            '',
            Field("birth_date", wrapper_class='row', placeholder='1998-09-24'),
            Field("country", wrapper_class='row'),
            Field("position_raw", wrapper_class='row'),
            Field("team_club_league_voivodeship_ver", wrapper_class='row'),
        )

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget()}
        fields = models.PlayerProfile.VERIFICATION_FIELDS + ['position_raw']


class PlayerProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        # self.helper.form_show_errors = True
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.wrapper_class = 'row'
        self.helper.label_class = 'col-md-3 text-md-right text-muted upper'
        self.helper.field_class = 'col-md-6'
        self.helper.layout = Layout(
            Div(
                Div(
                    Fieldset(
                        _('<h2 class="form-section-title">Podstawowe Informacje</h2>'),
                        Div(
                            Field('birth_date', wrapper_class='row'),
                            Field('league', wrapper_class='row', readonly=True),
                            # Field('club', wrapper_class='row', readonly=True),  # @todo kicked-off due to waiting for club mapping implemnetaiton into data_player.meta
                            Field('voivodeship', wrapper_class='row', readonly=True),
                            Field('team', wrapper_class='row', readonly=True),
                            Field('country', wrapper_class='row'),
                            Field("height", wrapper_class='row'),
                            Field("weight", wrapper_class='row'),
                            Field("address", wrapper_class='row'),
                            Field("about", wrapper_class='row'),

                        ),
                        css_class='col-md-6',
                    ),
                    Fieldset(
                        _('<h2 class="form-section-title">Piłkarskie szczegóły</h2>'),
                        Div(
                            Field('position_raw', wrapper_class='row'),
                            Field("position_raw_alt", wrapper_class='row'),
                            Field("formation", wrapper_class='row'),
                            Field("formation_alt", wrapper_class='row'),
                            Field("prefered_leg", wrapper_class='row'),
                            Field("practice_distance", wrapper_class='row'),

                            ),
                        css_class='col-md-6',
                    ),
                    css_class='row',
                ),
                Div(
                     Fieldset(
                        _('<h2 class="form-section-title">Piłkarski status</h2>'),
                        Div(
                            Field('transfer_status', wrapper_class='row'),
                            Field("card", wrapper_class='row'),
                            Field("soccer_goal", wrapper_class='row'),
                            Field("training_ready", wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                    Fieldset(
                        _('<h2 class="form-section-title">Dane kontaktowe</h2>'),
                        Div(
                            Field('phone', placeholder='+48 111 222 333', wrapper_class='row'),
                            Field('facebook_url', wrapper_class='row'),
                            Field("laczynaspilka_url", wrapper_class='row'),
                            Field("min90_url", wrapper_class='row'),
                            Field("transfermarket_url", wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                     # fieldset
                    css_class='row'
                ),  # div
                # css_class='card',
            )  # div master div
        )  # layout

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget()}
        fields = models.PlayerProfile.COMPLETE_FIELDS + models.PlayerProfile.OPTIONAL_FIELDS + ['country', 'birth_date']
