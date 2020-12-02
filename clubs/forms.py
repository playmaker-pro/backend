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


class ClubForm(forms.ModelForm):
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
                            Field('name', wrapper_class='row'),
                            Field('picture', wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                    Fieldset(
                        _('<h2 class="form-section-title">Zespoły</h2>'),
                        Div(
                            Field('editors', wrapper_class='row'),

                            ),
                        css_class='col-md-6',
                    ),
                    css_class='row',
                ),

                # css_class='card',
            )  # div master div
        )  # layout

    class Meta:
        model = models.Club

        fields = ['name', 'picture', 'editors']



class TeamForm(forms.ModelForm):
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
                            Field('name', wrapper_class='row'),
                            Field('travel_refunds', wrapper_class='row'),
                            Field('game_bonus', wrapper_class='row'),
                            Field('scolarships', wrapper_class='row'),
                            Field('gloves_shoes_refunds', wrapper_class='row'),
                            Field('regular_gear', wrapper_class='row'),
                            Field('secondary_trainer', wrapper_class='row'),
                            Field('diet_suplements', wrapper_class='row'),
                            Field('fizo', wrapper_class='row'),
                        ),
                        css_class='col-md-6',
                    ),
                    css_class='row',
                ),

                # css_class='card',
            )  # div master div
        )  # layout

    class Meta:
        model = models.Team

        fields = models.Team.EDITABLE_FIELDS
#  [
#         'picture',
#         'travel_refunds',
#         'game_bonus',
#         'scolarships',
#         'gloves_shoes_refunds',
#         'traning_gear',
#         'regular_gear',
#         'secondary_trainer',
#         'fizo',
#         'diet_suplements'
#     ]