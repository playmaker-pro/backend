from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.users.forms import UserCreationForm, UserEditForm
from .models import User
from django.conf import settings

from allauth.account.adapter import get_adapter
from allauth.account.utils import (
    filter_users_by_email,
    get_user_model,
    perform_login,
    setup_user_email,
    sync_user_email_addresses,
    url_str_to_user_pk,
    user_email,
    user_pk_to_url_str,
    user_username,
)


# allauth custom forms
class CustomSignupForm(SignupForm):

    first_name = forms.CharField(max_length=20, label='First Name')
    last_name = forms.CharField(max_length=20, label='Last Name')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    # rodo = forms.BooleanField(required=True)
    # rules = forms.BooleanField(required=True)
    # club = forms.CharField(max_length=355, label='Club')

    def save(self, request):
        adapter = get_adapter(request)
        user = adapter.new_user(request)

        # Here is access to pre-saved user model role - just to set proper Profile for user declared_type
        user.declared_role = self.cleaned_data['role']

        # Below paramters will be visible in post_save under User signal to assign Profile
        adapter.save_user(request, user, self)  # here kicks first object save()

        self.custom_signup(request, user)
        # TODO: Move into adapter `save_user` ?
        setup_user_email(request, user, [])  # this will trigger pre-mature Fk relation assign (if User model is not saved before)

        #if self.cleaned_data['club']:
        #    user.declared_club = self.cleaned_data['club']
        #user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user

    def save2222(self, request):
        user = super(CustomSignupForm, self).save(request)

        user.declared_role = self.cleaned_data['role']

        # if self.cleaned_data['club']:
        #    user.declared_club = self.cleaned_data['club']
        # user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


# wagtail custom user
class CustomUserEditForm(UserEditForm):
    declared_role = forms.ChoiceField(required=True, label=_("Declared Role"), choices=User.ROLE_CHOICES)
    # status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))


class CustomUserCreationForm(UserCreationForm):
    declared_role = forms.ChoiceField(required=True, label=_("Declared Role"), choices=User.ROLE_CHOICES)
    # status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))
