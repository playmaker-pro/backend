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
from .models import Product, Request, Tag


User = get_user_model()


logger = logging.getLogger(__name__)


from app.base.views import BasePMView
from .view_mixins import ProductFilterMixn


class BasePMProductView(BasePMView, ProductFilterMixn):
    pass


class SendRequestView(LoginRequiredMixin, View):
    '''Fetch form for annoucments'''
    http_method_names = ['post']

    def post(self, request, id, *args, **kwargs):
        user = self.request.user
        product = Product.objects.get(id=id)
        r = Request.objects.create(
            user=user,
            raw_body=request.POST,
            product=product,
        )
        messages.success(request, _("Twoje zgłoszenie zostało wysłane"))
        r.send_notification_to_admin()
        r.send_notifcation_to_user()

        return redirect("products:products")


class ProductView(BasePMProductView):
    page_title = 'Produkty Piłkarskie'
    template_name = "products/detail.html"

    def get_filters_values(self):
        return {'tags': list(Tag.objects.filter(active=True).values_list('name', flat=True)),}

    def get(self, request, slug, *args, **kwargs):
        kwargs['page_obj'] = get_object_or_404(Product, slug=slug)
        self.prepare_kwargs(kwargs)
        return super().get(request, *args, **kwargs)


class ProductTailsView(BasePMProductView):
    queryset = Product.objects.all()
    template_name = "products/base.html"
    paginate_limit = 9
    table_type = None
    page_title = 'Produkty Piłkarskie'

    def filter_queryset(self, queryset):
        queryset = queryset.filter(active=True)
        if self.filter_tag is not None:
            queryset = queryset.filter(tags__name=self.filter_tag)
        return queryset

    def get_filters_values(self):  # @todo add cache from Redis here
        return {'tags': list(Tag.objects.filter(active=True).values_list('name', flat=True)),}

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        paginator = Paginator(queryset, self.paginate_limit)
        page_number = request.GET.get('page') or 1
        page_obj = paginator.get_page(page_number)
        kwargs['page_obj'] = page_obj
        try:
            desc = PageDescription.objects.all().first()
        except Exception as e:
            desc = None
        kwargs['page_desc'] = desc
        kwargs['type'] = self.table_type
        self.prepare_kwargs(kwargs)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        return super().get(request, *args, **kwargs)
