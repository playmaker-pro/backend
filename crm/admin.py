from django.contrib import admin
from .models import *
from utils import linkify
from django.utils.translation import gettext_lazy as _
from .filters import *

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
                "created_by",
                "date_created",
                "updated_by",
                "date_updated",
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

    readonly_fields = ("created_by", "date_created", "updated_by", "date_updated",)
    
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

    search_fields = ["first_name", "last_name",]

    list_display_links = ("id", "full_name")

    list_filter = (
        IsActual,
        "club__voivodeship", 
        "team__league__highest_parent",
        HasPhone,
        HasEmail,
        HasClub,
        HasTeam,
        HasUser,
        CreatedBy,
        )

    def get_search_results(self, request, queryset, search_term):
        original_qs = queryset
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:            
            get_clubs_from_team_term = [team.club for team in Team.objects.filter(name__icontains=search_term)]
            get_all_teams = Team.objects.filter(club__in=get_clubs_from_team_term)
            queryset |= self.model.objects.filter(team__in=get_all_teams)
        queryset = queryset & original_qs
        return queryset, use_distinct

    def save_model(self, request, obj, form, change):
        if obj.id == None:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

# @admin.register(Demand)
class DemandAdminInline(admin.StackedInline):
    model = Demand

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    
    fieldsets = (
        ("Contact data", {
            "fields": (
                "lead",
                "contact_method",
                "contact_purpose",
                "by_who",
                "is_done",
                "reminding_contact",
                "created_by",
                "date_created",
                "updated_by",
                "date_updated",
                )
            }
        ),
        ("Details", {
            "fields": (
                "note",
                "todo"
                )
            }
        ),
        ("Demand conditions", {
            "fields": (
                "financial_conditions_from",
                "financial_conditions_to",
                "city",
                "range",
                )
            }
        ),     
    )

    search_fields = ["lead__first_name", "lead__last_name",]

    readonly_fields = ("created_by", "date_created", "updated_by", "date_updated",)

    list_display = (
        "id",
        linkify("lead"),
        "contact_method",
        "contact_purpose",
        linkify("by_who"),
        "is_done",
        "reminding_contact",
        linkify("created_by"),
        "date_created",
        linkify("updated_by"),
        "date_updated",
    )

    list_filter = (
        IsActual,
        "lead__club__voivodeship", 
        "lead__team__league__highest_parent",
        HasPhone,
        HasEmail,
        HasClub,
        HasTeam,
        HasUser,
        CreatedBy,
    )

    inlines = [DemandAdminInline,]

    def get_search_results(self, request, queryset, search_term):
        original_qs = queryset
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:            
            get_clubs_from_team_term = [team.club for team in Team.objects.filter(name__icontains=search_term)]
            get_all_teams = Team.objects.filter(club__in=get_clubs_from_team_term)
            queryset |= self.model.objects.filter(lead__team__in=get_all_teams)
        queryset = queryset & original_qs
        return queryset, use_distinct

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "lead":
            actual_leads = LeadStatus.objects.filter(is_actual=True)
            kwargs["queryset"] = actual_leads
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.id == None:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    pass