from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View, generic

from . import forms, models


def get_profile_form_model(user):
    if user.declared_role == 'P':
        return forms.PlayerProfileForm

    elif user.declared_role == 'T':
        return forms.CoachProfileForm

    elif user.declared_role == 'G':
        return forms.GuestProfileForm

    elif user.declared_role == 'C':
        return forms.ClubProfileForm

    elif user.declared_role == 'S':
        return forms.StandardProfileForm

    else:
        return forms.ProfileForm


def get_profile_model(user):
    if user.declared_role == 'P':
        return models.PlayerProfile
    elif user.declared_role == 'T':
        return models.CoachProfile
    elif user.declared_role == 'G':
        return models.GuestProfile
    elif user.declared_role == 'C':
        return models.ClubProfile
    elif user.declared_rol == 'S':
        return models.StandardProfile
    else:
        return models.StandardProfile


def get_profile_model_from_slug(slug):
    if slug.startswith('player'):
        return models.PlayerProfile
    elif slug.startswith('coach'):
        return models.CoachProfile
    elif slug.startswith('club'):
        return models.ClubProfile
    elif slug.startswith('guest'):
        return models.GuestProfile
    elif slug.startswith('standard'):
        return models.StandardProfile
    else:
        return models.StandardProfile


class ShowProfile(generic.TemplateView):
    template_name = "profiles/show_profile.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug:
            profile_model = get_profile_model_from_slug(slug)
            profile = get_object_or_404(profile_model, slug=slug)
            user = profile.user
        else:
            user = self.request.user

        # what happend when user is seeing his own profile.
        if user == self.request.user:
            kwargs["editable"] = True
            if user.declared_role is None:  # @todo - this is  not pretty.
                kwargs["role_form"] = self.get_role_declaration_form()
        kwargs["show_user"] = user

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        role_form = self.get_role_declaration_form()(request.POST)
        if role_form.is_valid():
            user.declared_role = role_form.cleaned_data['new']
            user.save()
            messages.success(request, "Gratulujemy. Profil użytkownika wybrany!")
        return redirect("profiles:show_self")

    def get_role_declaration_form(self):
        return forms.DeclareRoleForm


class RequestRoleChange(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        user = self.request.user
        if "cancel" in self.request.POST:
            qs = models.RoleChangeRequest.objects.filter(user=user, approved=False)
            for q in qs:
                q.delete()
            messages.success(request, "Cofnięto prośbe o zmianę roli.")
        else:
            post_values = request.POST.copy()
            post_values['user'] = user

            role_form = forms.ChangeRoleForm(post_values)
            if role_form.is_valid():
                role_form.save()
            messages.success(request, "Przyjęto zgloszenie o nową role.")
        return redirect("profiles:show_self")


class EditProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/edit_profile.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)

        if "profile_form" not in kwargs:
            profile_form = get_profile_form_model(user)
            kwargs["profile_form"] = profile_form(instance=user.profile)

        if "role_form" not in kwargs:
            kwargs["role_form"] = forms.ChangeRoleForm()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        user_form = forms.UserForm(
            request.POST,
            request.FILES,
            instance=user)

        profile_form = get_profile_form_model(user)(
            request.POST,
            request.FILES,
            instance=user.profile
        )

        if not (user_form.is_valid() and profile_form.is_valid()):
            messages.error(
                request,
                "There was a problem with the form. " f"Please check the details. 1{user_form.errors} 2{profile_form.errors}",
            )
            user_form = forms.UserForm(instance=user)
            profile_form = get_profile_form_model(user)(instance=user.profile)
            return super().get(request, user_form=user_form, profile_form=profile_form, role_form=forms.ChangeRoleForm())

        # Both forms are fine. Time to save!
        user_form.save()
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()
        messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")
