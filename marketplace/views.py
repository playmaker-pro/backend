# external dependencies
import json
import logging
import math
import operator
from functools import reduce

from clubs.models import Club, Team
from crispy_forms.utils import render_crispy_form
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from app import mixins
from profiles.utils import get_datetime_from_age
from roles import definitions
from stats import adapters
from users.models import User

from .forms import AnnouncementForm

from .models import Announcement



User = get_user_model()


logger = logging.getLogger(__name__)



class AddAnnouncementView(LoginRequiredMixin, View):
    http_method_names = ['post', 'get']

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_coach or user.is_club:
            form = AnnouncementForm()
        else:
            return JsonResponse({})
        data = {}
        data['form'] = render_crispy_form(form)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_coach or user.is_club:
            form = AnnouncementForm(request.POST)

        data = {'success': False, 'redirection_url': None, 'form': None}

        if form.is_valid():
            form.save()
            messages.success(request, _("Przyjęto ogłoszenia."))

            data['success'] = True
            data['redirection_url'] = reverse("marketplace:announcements")
            return JsonResponse(data)
        else:
            data['form'] = render_crispy_form(form)
            return JsonResponse(data)


class AnnouncementsView(generic.TemplateView, mixins.ViewModalLoadingMixin):
    template_name = "marketplace/base.html"
    http_method_names = ["get"]
    paginate_limit = 15
    table_type = None
    page_title = 'Ogłoszenia piłkarskie'

    def filter_queryset(self, queryset):
        return queryset

    def get_queryset(self):
        return Announcement.objects.filter(status__in=Announcement.ACTIVE_STATES)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        # kwargs['ammount'] = page_obj.count()
        return super().get(request, *args, **kwargs)
