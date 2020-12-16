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


class UserMissingNameForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True  # '<i class="icofont-map"></i>'
        self.helper.label_class = 'col-md-2 p-1'
        self.helper.field_class = 'col-12 p-1'
        self.helper.layout = Layout(
            Fieldset(
                '',
                Div(             
                    Div(
                        Field('first_name', css_class="row"),
                        Field('last_name', css_class="row"),

                    ),
                    # css_class='card',
                ),
            )
        )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


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
                    # css_class='card',
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


class BaseProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        # self.helper.form_show_errors = True
        self.helper.error_text_inline = True
        self.helper.labels_uppercase = True
        self.helper.wrapper_class = 'row'
        self.helper.label_class = 'col-md-4 text-md-right text-muted upper form-label'
        self.helper.field_class = 'col-md-6'


class UserBasicForm(BaseProfileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Fieldset(
                _('<h2 class="form-section-title">Dane osobowe</h2>'),

                Field('first_name', wrapper_class='row', placeholder='imię'),
                Field('last_name', wrapper_class='row', placeholder='nazwisko'),
                Field('picture', wrapper_class='row'),
                css_class='col',
            ),
        )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'picture']


class ClubProfileForm(BaseProfileForm):
    class Meta:
        model = models.ClubProfile
        fields = ['club_role']


class CoachProfileForm(BaseProfileForm):
    # birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for fieldname in ['club_role', 'league', 'team']:
        #     self.fields[fieldname].help_text = None
        self.helper.layout = Layout(
            Div(
                Div(
                    # Fieldset(
                    #     _('<h2 class="form-section-title">Klub</h2>'),
                    #     Div(
                    #         Field('club_role', wrapper_class='row', placeholder='Jaką role pełnisz w klubie'),
                    #     ),
                    #     css_class='col-md-6',
                    # ),
                    Fieldset(
                        _('<h2 class="form-section-title">Podstawowe Informacje</h2>'),
                        Div(
                            Field('birth_date', wrapper_class='row', css_class=self.get_mandatory_field_class("birth_date"),),
                            # Field('league', wrapper_class='row', readonly=True),
                            # # Field('club', wrapper_class='row', readonly=True),  # @todo kicked-off due to waiting for club mapping implemnetaiton into data_player.meta
                            # Field('voivodeship', wrapper_class='row', readonly=True),
                            # Field('team', wrapper_class='row', readonly=True),
                            # Field('country', wrapper_class='row'),
                            Field("address", wrapper_class='row'),
                            Field("about", wrapper_class='row'),

                        ),
                        css_class='col-md-6',
                    ),
                    Fieldset(
                        _('<h2 class="form-section-title">Dane kontaktowe</h2>'),
                        Div(
                            Field('phone', placeholder='+48 111 222 333', wrapper_class='row', css_class='mandatory'),
                            Field('facebook_url', wrapper_class='row'),
                            Field("soccer_goal", wrapper_class='row'),
                            Field("practice_distance", wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                    css_class='row',
                ),
                # css_class='card',
            )  # div master div
        )  # layo

    class Meta:
        model = models.CoachProfile
        fields = ['club_role', 'country', 'address', 'about', 'birth_date', 'facebook_url', 'soccer_goal', 'phone', 'practice_distance'] #'league', 'voivodeship', 'team',
    
    def get_mandatory_field_class(self, field_name):
        if field_name in models.CoachProfile.VERIFICATION_FIELDS:
            return 'mandatory-field'


class PlayerProfileForm(BaseProfileForm):
    # birth_date = forms.DateField(input_formats=['%Y-%m-%d'], widget=widgets.BootstrapDateTimePickerInput())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Fieldset(
                _('<h2 class="form-section-title">Piłkarski status</h2>'),
                Field('transfer_status', wrapper_class='row'),
                Field("card", wrapper_class='row'),
                Field("soccer_goal", wrapper_class='row'),
                Field("training_ready", wrapper_class='row'),
                css_class='col-md-6',
            ),
            Fieldset(
                _('<h2 class="form-section-title">Podstawowe Informacje</h2>'),
                Field('birth_date', wrapper_class='row', css_class='mandatory'),
                # Field('league', wrapper_class='row', readonly=True),
                # # Field('club', wrapper_class='row', readonly=True),  # @todo kicked-off due to waiting for club mapping implemnetaiton into data_player.meta
                # Field('voivodeship', wrapper_class='row', readonly=True),
                # Field('team', wrapper_class='row', readonly=True),
                Field('country', wrapper_class='row', css_class='mandatory'),
                Field("height", wrapper_class='row', placeholder='130 - 210 cm', css_class='mandatory'),
                Field("weight", wrapper_class='row', placeholder='40 - 140 kg', css_class='mandatory'),
                Field("address", wrapper_class='row'),
                Field("about", wrapper_class='row'),
                css_class='col-md-6',
            ),
            Fieldset(
                _('<h2 class="form-section-title">Piłkarskie szczegóły</h2>'), 
                Field('position_raw', wrapper_class='row', css_class='mandatory'),
                Field("position_raw_alt", wrapper_class='row'),
                Field("formation", wrapper_class='row', css_class='mandatory'),
                Field("formation_alt", wrapper_class='row'),
                Field("prefered_leg", wrapper_class='row', css_class='mandatory'),
                Field("practice_distance", wrapper_class='row', css_class='mandatory'),
                css_class='col-md-6',
            ),

            Fieldset(
                _('<h2 class="form-section-title">Współpraca</h2>'),
                Field('agent_status', wrapper_class='row'),
                Field("agent_name", wrapper_class='row'),
                Field("agent_phone", wrapper_class='row'),
                css_class='col-md-6',
            ),
            Fieldset(
                _('<h2 class="form-section-title">Dane kontaktowe</h2>'),
                Field('phone', placeholder='+48 111 222 333', wrapper_class='row', css_class='mandatory'),
                Field('facebook_url', wrapper_class='row'),
                Field("laczynaspilka_url", wrapper_class='row'),
                Field("min90_url", wrapper_class='row'),
                Field("transfermarket_url", wrapper_class='row'),
                css_class='col-md-6',
            ),
            Fieldset(
                _('<h2 class="form-section-title">Promo Video</h2>'),
                Field('video_url', wrapper_class='row', placeholder=_('youtube url')),
                Field('video_title', wrapper_class='row', placeholder=_('Tytuł')),
                Field("video_description", wrapper_class='row', placeholder=_('Opisz w której minucie dzieją się istotne rzeczy')),
                Field('video_url_second', wrapper_class='row', placeholder=_('youtube url nr 2')),
                Field('video_title_second', wrapper_class='row', placeholder=_('Tytuł nr 2')),
                Field("video_description_second", wrapper_class='row', placeholder=_('Nr 2 Opisz w której minucie dzieją się istotne rzeczy')),
                Field('video_url_third', wrapper_class='row', placeholder=_('youtube url nr 3')),
                Field('video_title_third', wrapper_class='row', placeholder=_('Tytuł nr 3')),
                Field("video_description_third", wrapper_class='row', placeholder=_('Nr 3 Opisz w której minucie dzieją się istotne rzeczy')),
                
                css_class='col-md-6',
            ),
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
        # self.fields['team_club_league_voivodeship_ver'].required = True
        # self.fields['league_raw'].label = False  # '<i class="icofont-ui-user-group"></i>'
        self.fields['country'].help_text = None
        self.fields['club_raw'].help_text = None
        self.fields['league_raw'].label = 'Klub'
        self.fields['league_raw'].help_text = None
        self.fields['league_raw'].label = 'Poziom rozgrywkowy'
        self.fields['voivodeship_raw'].help_text = None
        self.fields['voivodeship_raw'].label = 'Wojewódźtwo'
        self.fields['practice_distance'].help_text = None
        self.fields['practice_distance'].label = 'Odległość na treningi'

        self.fields['bio'].help_text = None
        self.fields['bio'].label = 'Krótko o sobie'

        self.fields['address'].help_text = None
        self.fields['facebook_url'].help_text = None

        self.helper.layout = Layout(
            Fieldset(
                _('<h2 class="form-section-title">Podstawowe Informacje</h2>'),
                Field('bio', wrapper_class='row',),
                Field('soccer_goal', wrapper_class='row', css_class='mandatory'),
                Field('league_raw', wrapper_class='row', placeholder='deklarowany'),
                Field('club_raw', wrapper_class='row', placeholder='reprezentowany'),
                Field('voivodeship_raw', wrapper_class='row', placeholder='deklarowane'),
                Field('country', wrapper_class='row'),
                Field("practice_distance", wrapper_class='row', placeholder='maksymalna w km'),
                css_class='col-md-6',
            ),
            Fieldset(
                _('<h2 class="form-section-title">Dane kontaktowe</h2>'),
                Field("address", wrapper_class='row', placeholder='np. Dolnyśląsk, Wrocław'),
                Field('facebook_url', wrapper_class='row', placeholder='https://facebook..'),
                css_class='col-md-6',
            ),
        )  # layout

    class Meta:
        model = models.ScoutProfile
        widgets = {'country': CountrySelectWidget()}
        fields = model.COMPLETE_FIELDS + model.OPTIONAL_FIELDS + ['bio']


class GuestProfileForm(BaseProfileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].help_text = None
        self.fields['bio'].label = 'Krótko o sobie'

        self.helper.layout = Layout(
            Fieldset(
                _('<h2 class="form-section-title">Dane kontaktowe</h2>'),
                Field('facebook_url', wrapper_class='row', placeholder='https://facebook...'),
                Field('bio', wrapper_class='row',),
                css_class='col-md-6',
            )
        )

    class Meta:
        model = models.GuestProfile
        fields = ['facebook_url', 'bio']


class ParentProfileForm(GuestProfileForm):
    class Meta:
        model = models.ManagerProfile
        fields = ['facebook_url', 'bio']


class ManagerProfileForm(GuestProfileForm):
    class Meta:
        model = models.ManagerProfile
        fields = ['facebook_url', 'bio']
