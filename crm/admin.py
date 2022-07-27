from django.contrib import admin
from .models import *
from utils import linkify

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass

@admin.register(ContactPurpose)
class ContactPurposeAdmin(admin.ModelAdmin):
    pass

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
        "full_name",
        linkify("user"),
        "phone",
        "email",
        "user_role",
        linkify("team"),
        linkify("club"),
        "is_actual",
        "data_mapper_id",
        "twitter_url",
        "facebook_url",
        "linkedin_url",
        "instagram_url",
        "website_url",
        linkify("created_by"),
        "date_created",
        linkify("updated_by"),
        "date_updated",        
        linkify("previous"),
        linkify("next"),
    )

    list_display_links = ("id", "full_name")

    list_filter = ["is_actual"]

    def save_model(self, request, obj, form, change):
        if obj.id == None:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        if obj.id == None:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)