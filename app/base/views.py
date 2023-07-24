import json
import logging
import math
import operator
from functools import reduce

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

from app import mixins


User = get_user_model()


class BasePMView(
    generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin
):
    http_method_names = ["get"]

    def prepare_kwargs(self, kwargs):
        kwargs["modals"] = self.modal_activity(
            self.request.user, register_auto=False, verification_auto=False
        )
        kwargs["page_title"] = self.page_title
        kwargs["filters"] = self.get_filters_values()

    def get_queryset(self):
        return self.queryset

    def filter_queryset(self):
        pass

    def get_filters_values(self):
        pass
