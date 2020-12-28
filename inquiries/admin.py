from django.contrib import admin
from . import models


@admin.register(models.InquiryPlan)
class InquiryPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'default', 'limit')


@admin.register(models.UserInquiry)
class UserInquiryAdmin(admin.ModelAdmin):
    search_fields = ('user__email',)


@admin.register(models.InquiryRequest)
class InquiryRequestAdmin(admin.ModelAdmin):
    search_fields = ('recipient__email', 'sender__email',)
