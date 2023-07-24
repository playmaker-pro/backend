# external dependencies
import json
import logging
import math
import operator
from functools import reduce

from clubs.models import Club, Team, Seniority, League, Gender, Voivodeship
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
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from followers.models import Follow, FollowTeam
from inquiries.models import InquiryRequest
from app import mixins
from profiles.utils import get_datetime_from_age
from roles import definitions
from stats import adapters
from users.models import User
from notifications import message
from profiles.models import PlayerPosition
from .models import QuestionAnswer


User = get_user_model()


logger = logging.getLogger(__name__)


class FaqView(
    generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin
):
    page_title = "Najczęściej zadawane pytania"
    template_name = "fqa/base.html"

    def get(self, request, *args, **kwargs):
        kwargs["objects"] = QuestionAnswer.objects.filter(visible=True)
        kwargs["page_title"] = self.page_title
        kwargs["modals"] = self.modal_activity(
            request.user, register_auto=False, verification_auto=False
        )
        return super().get(request, *args, **kwargs)
