import logging

from crispy_forms.utils import render_crispy_form

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from profiles import forms
from django.http import Http404, JsonResponse

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

User = get_user_model()


logger = logging.getLogger(__name__)


class AccountVerification(LoginRequiredMixin, View):

    http_method_names = ["post", "get"]

    def get(self, request, *args, **kwargs):
        user = request.user
        if request.user.is_coach:
            form = forms.CoachVerificationForm(instance=user.profile)
        if request.user.is_club:
            form = forms.ClubVerificationForm(instance=user.profile)
        if request.user.is_player:
            form = forms.PlayerVerificationForm(instance=user.profile)
        data = {}
        data["form"] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile

        if request.user.is_coach:
            form = forms.CoachVerificationForm
        if request.user.is_club:
            form = forms.ClubVerificationForm
        if request.user.is_player:
            form = forms.PlayerVerificationForm
        
        if not form:
            raise Http404

        form = form(request.POST, instance=profile)

        data = {"success": False, "url": None, "form": None}

        if form.is_valid():
            form.save()
            user.unverify()
            user.save()
            messages.success(
                request,
                _("Przyjęto zgłoszenie weryfikacji konta."),
                extra_tags="alter-success",
            )

            data["success"] = True
            data["url"] = reverse("profiles:show_self")
            return JsonResponse(data)
            # return redirect(reverse("profiles:show_self"))
        else:
            # response_data = {} d
            # messages.success(request, _("Błędnie wprowadzone dane."), extra_tags='alter-success')
            # request.session['verification_form_errors'] = verification_form.errors
            data["form"] = render_crispy_form(form)
            return JsonResponse(data)
            # redirect('profiles:show_self')
