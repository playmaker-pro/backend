from django.contrib import admin
from .models import LeadStatus
from utils import linkify

@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Lead information", {
            "fields": (
                "first_name",
                "last_name",
                "user",
                "club",
                "team",
                )
            }
        ),
        ("Contact", {
            "fields": (
                "phone",
                "email"
                )
            }
        ),
        ("Socials", {
            "fields": (
                "facebook_url",
                "twitter_url",
                "linkedin_url",
                "instagram_url",
                "website_url",
                )
            }
        ),
    )
    
    list_display = (
        "id",
        "first_name",
        "last_name",
        linkify("user"),
        linkify("club"),
        linkify("team"),
        "date_created",
        "date_updated",
        linkify("created_by"),
        linkify("updated_by"),
        "is_actual",
        linkify("previous"),
        linkify("next"),
    )

    list_filter = ["is_actual"]

    def save_model(self, request, obj, form, change):
        if obj.id == None:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)