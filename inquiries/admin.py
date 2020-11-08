from django.contrib import admin
from . import models 


@admin.register(models.InquiryPlan)
class InquiryPlanAdmin(admin.ModelAdmin):
    pass 


@admin.register(models.UserInquiry)
class UserInquiryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.InquiryRequest)
class InquiryRequestAdmin(admin.ModelAdmin):
    pass
