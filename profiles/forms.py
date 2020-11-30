from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Field, MultiField
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, Tab, TabHolder, Alert
from django.contrib.auth import get_user_model
from profiles import models
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class ChangeRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.wrapper_class = 'row'
        self.helper.label_class = 'col-md-6'
        self.helper.field_class = 'col-md-6'

        self.helper.layout = Layout(
            Div(
                Div(
                    Fieldset(
                        '',  #_('<h2 class="form-section-title">Zmien role w serwisie</h2>'),
                        Div(
                            Field('new', wrapper_class='row', selected='T'),
                        ),
                        css_class='',
                    ),  # fieldset
                    css_class=''
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
                        Field('first_name', css_class="col-sm-6"),
                        Field('last_name', css_class="col-sm-6"),
                        Field('email', css_class="col-sm-6", readonly=True),
                        Field('picture', css_class="col-sm-6", ),
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
    '''Basic profile account which covers basic setup off account
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("bio"),
            Submit("update", "Update", css_class="btn-success"),
        )

    class Meta:
        model = models.GuestProfile
        fields = ["bio"]


phone_number_format = "+[0-9] [0-9]{3}-[0-9]{3}-[0-9]{3}"


class CoachProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
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
                            Field("address", wrapper_class='row'),
                            Field("about", wrapper_class='row'),

                        ),
                        css_class='col-md-6',
                    ),

                    css_class='row',
                ),
                Div(
                    Fieldset(
                        _('<h2 class="form-section-title">Piłkarski status</h2>'),
                        Div(
                            Field('phone', placeholder='+48 111 222 333', wrapper_class='row'),
                            Field('facebook_url', wrapper_class='row'),
                            Field("soccer_goal", wrapper_class='row'),
                            Field("practice_distance", wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                    # fieldset
                    css_class='row'
                ),  # div
                # css_class='card',
            )  # div master div
        )  # layo

    class Meta:
        model = models.CoachProfile
        fields = ["league", "voivodeship", "team", "country", "address", "about", "birth_date", "facebook_url", "soccer_goal", "phone", "practice_distance"]


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
        self.fields['team_club_league_voivodeship_ver'].required = True


class ClubVerificationForm(VerificationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team_club_league_voivodeship_ver'].required = True
        self.fields['team_club_league_voivodeship_ver'].label = 'Który klub reprezentujesz'

        self.helper.layout = Fieldset(
            '',
            Field("team_club_league_voivodeship_ver", wrapper_class='row'),
        )

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget()}
        fields = models.ClubProfile.VERIFICATION_FIELDS

from django.forms import DateTimeInput


class BootstrapDateTimePickerInput(DateTimeInput):
    template_name = 'profiles/widgets/bootstrap_datetimepicker.html'

    def get_context(self, name, value, attrs):
        datetimepicker_id = 'datetimepicker_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        attrs['data-target'] = '#{id}'.format(id=datetimepicker_id)
        attrs['class'] = 'form-control datetimepicker-input'
        context = super().get_context(name, value, attrs)
        context['widget']['datetimepicker_id'] = datetimepicker_id
        return context

class CoachVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=BootstrapDateTimePickerInput())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].required = True
        self.fields['country'].required = True
        self.fields['country'].initial = 'PL'
        self.fields['team_club_league_voivodeship_ver'].label = 'Który klub/drużynę reprezentujesz'
        self.helper.layout = Fieldset(
            '',
            Div(
                Field("birth_date", wrapper_class='row', placeholder='1998-09-24', id="datetimepicker1"),
                css_class="input-group date",
            ),
            
            Field("country", wrapper_class='row'),
            Field("team_club_league_voivodeship_ver", wrapper_class='row'),
        )

    class Meta:
        model = models.PlayerProfile
        widgets = {'country': CountrySelectWidget()}
        fields = models.CoachProfile.VERIFICATION_FIELDS


class PlayerVerificationForm(VerificationForm):
    birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=BootstrapDateTimePickerInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].required = True
        self.fields['country'].required = True
        self.fields['country'].initial = 'PL'
        self.fields['position_raw'].required = True

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


class BaseProfileForm(forms.ModelForm):
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


class PlayerProfileForm(BaseProfileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                            Field("height", wrapper_class='row', placeholder='130 - 210 cm'),
                            Field("weight", wrapper_class='row', placeholder='40 - 140 kg'),
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
                        _('<h2 class="form-section-title">Współpraca</h2>'),
                        Div(
                            Field('agent_status', wrapper_class='row'),
                            Field("agent_name", wrapper_class='row'),
                            Field("agent_phone", wrapper_class='row'),
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
                    Fieldset(
                        _('<h2 class="form-section-title">Promo Video</h2>'),
                        Div(
                            Field('video_url', wrapper_class='row', placeholder=_('youtube url')),
                            Field('video_title', wrapper_class='row', placeholder=_('Tytuł')),
                            Field("video_description", wrapper_class='row', placeholder=_('Opisz w której minucie dzieją się istotne rzeczy')),
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


class ScoutProfileForm(BaseProfileForm):
    '''
    COMPLETE_FIELDS = ['soccer_goal']

    OPTIONAL_FIELDS = [
        'country',
        'facebook_url',
        'address',
        'practice_distance',
        'club',
        'league',
        'voivodeship',
        ]
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Div(
                Div(
                    Fieldset(
                        _('<h2 class="form-section-title">Podstawowe Informacje</h2>'),
                        Div(
                            Field('soccer_goal', wrapper_class='row'),
                            Field('facebook_url', wrapper_class='row'),
                            Field('league', wrapper_class='row',),
                            Field('club', wrapper_class='row'),  
                            Field('voivodeship', wrapper_class='row',),
                            Field('country', wrapper_class='row'),
                            Field("address", wrapper_class='row'),
                            Field("practice_distance", wrapper_class='row'),

                        ),
                        css_class='col-md-6',
                    ),
                    css_class='row',
                ),

                # css_class='card',
            )  # div master div
        )  # layout

    class Meta:
        model = models.ScoutProfile
        widgets = {'country': CountrySelectWidget()}
        fields = model.COMPLETE_FIELDS + model.OPTIONAL_FIELDS
