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


class ProductFilterMixn:

    @property
    def filter_tag(self):
        value = self.request.GET.get('tag')
        if value:
            return value
        return None


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
        r.mail_admins_about_new_product_request()
        r.send_notifcation_to_user()

        return redirect("products:products")
    #    et('id')

    #     if user.announcementuserquota.left <= 0 and not _id:
    #         return JsonResponse(data)
    #     if _id:
    #         a = Announcement.objects.get(id=int(_id))
    #         form = AnnouncementForm(request.POST, instance=a)
    #         if form.is_valid():
    #             ann = form.save(commit=False)
    #             ann.creator = request.user
    #             ann.save()
    #             form.save_m2m()
    #             messages.success(request, _("Ogłoszenia zaktualizowano"))

    #             data['success'] = True
    #             data['redirection_url'] = reverse("marketplace:announcements")
    #             return JsonResponse(data)
    #         else:

    #             data['form'] = render_crispy_form(form)
    #             return JsonResponse(data)
    #     else:
    #         if not user.announcementuserquota.can_make_request:
    #             return JsonResponse({'message': 'Limit ogłoszeń przekroczony.'})

    #         if user.is_coach or user.is_club:
    #             form = AnnouncementForm(request.POST)

    #         if form.is_valid():
    #             ann = form.save(commit=False)
    #             ann.creator = request.user
    #             ann.save()
    #             form.save_m2m()
    #             user.announcementuserquota.increment()
    #             user.announcementuserquota.save()
    #             messages.success(request, _("Przyjęto ogłoszenia."))

    #             data['success'] = True
    #             data['redirection_url'] = reverse("marketplace:announcements")
    #             return JsonResponse(data)
    #         else:
    #             data['form'] = render_crispy_form(form)
    #             return JsonResponse(data)


class ProductView(generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin, ProductFilterMixn):
    page_title = 'Produkty Piłkarskie'
    template_name = "products/detail.html"

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            'tags': list(Tag.objects.filter(active=True).values_list('name', flat=True)),

        }

    def get(self, request, id, *args, **kwargs):
        kwargs['page_obj'] = get_object_or_404(Product, id=id)
        kwargs['filters'] = self.get_filters_values()
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        return super().get(request, *args, **kwargs)


class ProductTailsView(generic.TemplateView, mixins.ViewModalLoadingMixin, mixins.ViewFilterMixin, ProductFilterMixn):
    template_name = "products/base.html"
    http_method_names = ["get"]
    paginate_limit = 9
    table_type = None
    page_title = 'Produkty Piłkarskie'

    def filter_queryset(self, queryset):
        queryset = queryset.filter(active=True)
        if self.filter_tag is not None:
            queryset = queryset.filter(tags__name=self.filter_tag)

        return queryset

    def get_queryset(self):
        return Product.objects.all()

    def get_filters_values(self):  # @todo add cache from Redis here
        return {
            'tags': list(Tag.objects.filter(active=True).values_list('name', flat=True)),
        }

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
        kwargs['page_title'] = self.page_title
        kwargs['type'] = self.table_type
        kwargs['filters'] = self.get_filters_values()
        kwargs['modals'] = self.modal_activity(request.user, register_auto=False, verification_auto=False)
        page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1
        return super().get(request, *args, **kwargs)
